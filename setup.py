from setuptools import setup, find_packages


def readme():
	with open('./README.md') as f:
		return f.read()


setup(
	name='bing',
	version='0.31',
	license='MIT',

	url='https://github.com/idin/bing',
	author='Idin',
	author_email='py@idin.ca',

	description='Python library for searching entites in Bing',
	long_description=readme(),
	long_description_content_type='text/markdown',

	classifiers=[
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Developers',
		'Programming Language :: Python :: 3 :: Only',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Topic :: Software Development :: Libraries :: Python Modules'
	],

	packages=find_packages(exclude=["jupyter_tests", ".idea", ".git"]),
	install_requires=['requests', 'memoria', 'chronology', 'disk'],
	python_requires='~=3.6',
	zip_safe=False
)
