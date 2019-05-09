from json import JSONDecodeError
from .BasicAPI import BasicAPI
from .normalize_company_name import normalize_company_name

try:
	from slytherin.collections import rename_dict_keys
except:
	from .rename_dict_keys import rename_dict_keys


class Bing(BasicAPI):
	def __init__(self):
		super().__init__(tokens=None, name='bing', wait_time=0.1)

	@staticmethod
	def url_func(name):
		return f'https://finance.services.appex.bing.com/Market.svc/MTAutocomplete?q={name}&locale=en%3Aus'

	def convert_name_response_to_dicts(self, response):
		mapping = {
			'DisplayName': 'display_name',
			'FriendlyName': 'friendly_name',
			'RT00S': 'other_name',
			'OS01W': 'full_name_1',
			'OS0LN': 'full_name_2',
			'RT0SN': 'full_name_3',
			'OS001': 'ticker',
			'AC040': 'exchange',
			'LS01Z': 'exchange_code',
			'RT0EC': 'country_code',
			'OS01V': 'language',
			'SecId': 'sector_id',
			'ExMicCode': 'primary_quote_mic',
			'FullInstrument': 'full_instrument',
			'OS05J': 'isin'
		}

		def _format_dictionary(d):
			result = rename_dict_keys(dictionary=d, mapping=mapping)
			result = {key.lower(): value for key, value in result.items()}
			result['api_name'] = self.name
			return result

		try:
			list_of_dictionaries = response.json()['data'].copy()
		except JSONDecodeError as e:
			self.append_exception({'func': 'convert_name_response_to_dicts', 'exception': e})
			return []

		return [_format_dictionary(dictionary) for dictionary in list_of_dictionaries]

	def search_name(self, name, convert_response=True, add_query_name=False, echo=0):
		echo = max(0, echo)
		normalized_name = normalize_company_name(name=name)

		def _condition_func(_response):
			if _response is None:
				return False
			else:
				try:
					_ = _response.json()['data']
					return True
				except:
					return False

		response = self.send_request(
			url_func=self.url_func, request_name='search_name', hashed_args={'name': normalized_name},
			condition_func=_condition_func, echo=echo
		)
		if convert_response:
			result = self.convert_name_response_to_dicts(response=response)
			if add_query_name:
				for entity in result:
					entity.update({'query_name': name})
			return result
		else:
			return response

	def search(
			self, name=None, ticker=None, country_code=None, exchange_code=None,
			greedy=True, add_query_values=False, echo=0
	):
		echo = max(0, echo)

		if name is None and ticker is None:
			raise ValueError('at least one of name or ticker should be given!')

		name = name or ticker
		entities = self.search_name(name=name, convert_response=True, add_query_name=add_query_values, echo=echo)
		result = []
		for entity in entities:
			distance = 0
			if ticker is not None:
				if add_query_values:
					entity['query_ticker'] = ticker
				if entity['ticker'] is None:
					distance += 0.5
				elif entity['ticker'].lower() != ticker.lower():
					distance += 1
					if not greedy:
						continue
			if country_code is not None:
				if add_query_values:
					entity['query_country_code'] = country_code
				if entity['country_code'] is None:
					distance += 0.5
				elif entity['country_code'].lower() != country_code.lower():
					distance += 1
					if not greedy:
						continue
			if exchange_code is not None:
				if add_query_values:
					entity['query_exchange_code'] = exchange_code
				if entity['exchange_code'] is None:
					distance += 0.5
				elif entity['exchange_code'].lower() != exchange_code.lower():
					distance += 1
					if not greedy:
						continue
			entity['result_distance'] = distance
			result.append(entity)

			result.sort(key=lambda x: x['result_distance'])
		return result
