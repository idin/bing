import warnings
import requests
from memoria import Box, Cache
from disk import get_path
from chronology import get_elapsed_seconds, get_now, get_today_str, sleep


class BasicAPI:
	def __init__(self, tokens, name, directory=None, wait_time=0.3):

		self._cache = Cache(path=get_path(directory=directory, file=f'{name}_cache'), num_tries=3)

		self._tokens = tokens
		if tokens is not None:
			self._token_box = Box(path=get_path(directory=directory, file=f'{name}_tokens'))
			if not self._token_box.contains('usage'):
				self._token_box.put(name='usage', obj={})

		self._last_request_time = get_now()
		self._wait_time = wait_time
		self._exceptions = []
		self._name = name

	@property
	def name(self):
		return self._name

	@property
	def exceptions(self):
		return self._exceptions.copy()

	def append_exception(self, e):
		self._exceptions.append(e)

	@property
	def usage(self):
		return self._token_box.get(name='usage')

	@property
	def usage_today(self):
		result = {}
		today = get_today_str()
		for token in self._tokens:
			result[token] = 0
			if token in self.usage:
				if today in self.usage[token]:
					result[token] = self.usage[token][today]
		return result

	def use(self, token):
		if token not in self.usage:
			self.usage[token] = {}

		today = get_today_str()
		if today in self.usage[token]:
			self.usage[token][today] += 1
		else:
			self.usage[token][today] = 1

	def choose_token(self):
		# find the token least used today
		return min(self.usage_today, key=self.usage_today.get)

	def send_url_request(self, url, token=None, verify=False, echo=0):
		"""
		:type url: str
		:type type: str
		:type echo: int
		"""
		echo = max(0, echo)
		if echo:
			print(f'requesting: "{url}"')

		elapsed = get_elapsed_seconds(start=self._last_request_time)
		if elapsed < self._wait_time:
			sleep(seconds=max(0, self._wait_time - elapsed))

		try:
			with warnings.catch_warnings():
				warnings.simplefilter("ignore")
				response = requests.get(url=url, verify=verify)

		except Exception as e:
			self.append_exception({'func': 'send_url_request', 'url': url, 'exception': e})
			response = None

		self._last_request_time = get_now()
		if token is not None:
			self.use(token=token)
		return response

	def send_request(
			self, url_func, request_name, hashed_args, unhashed_args=None,
			cache=True, use_cache=True, condition_func=lambda x: True, echo=0
	):
		"""
		:type hashed_args: dict
		:type unhashed_args: dict
		:type url_func: callable
		:type condition_func: callable
		:return:
		"""
		echo = max(0, echo)
		unhashed_args = unhashed_args or {}
		if 'token' in unhashed_args:
			token = unhashed_args['token']
		elif 'token' in hashed_args:
			token = hashed_args['token']
		else:
			token = None

		def _request_func(**_kwargs):
			return self.send_url_request(url=url_func(**_kwargs), token=token, echo=echo)

		if not cache:
			kwargs = unhashed_args.copy()
			kwargs.update(hashed_args)
			result = _request_func(**kwargs)
		else:
			cach_dict = self._cache.cache(
				func=_request_func, func_name=request_name, hashed_args=hashed_args, unhashed_args=unhashed_args,
				use_cache=use_cache, condition_func=condition_func, echo=echo-1
			)
			result = cach_dict['result']

		return result
