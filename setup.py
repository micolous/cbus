#!/usr/bin/env python

from setuptools import setup, find_packages
from platform import system
system = system().lower()

deps = [
	'configparser (>=3.7.0)',
	'serial (>=2.6)',
	'lxml (>=2.3.2)',
	'Twisted (>=12.0.0)',
	'six',
]

if system != 'windows':
	# Windows doesn't support some of these things so we run it in reduced
	# functionality mode.
	deps += [
		'daemon (>=1.0)',
		'pygobject (>=2.28.6)'
	]

tests_require = ['nose', 'pytype']

setup(
	name="cbus",
	version="0.2",
	description="Library and applications to interact with Clipsal CBus in Python.",
	author="Michael Farrell",
	author_email="micolous@gmail.com",
	url="https://github.com/micolous/cbus",
	license="LGPL3+",
	requires=deps,
	test_suite='nose.collector',
	tests_require=tests_require,
	extras_require={'test': tests_require},
	# TODO: add scripts to this.
	packages=find_packages(),
	
	entry_points={
		'console_scripts': [
			'cbz_dump_labels = cbus.toolkit.dump_labels:main',
			'cmqttd = cbus.daemon.cmqttd:main',
			'cbus_fetch_protocol_docs = cbus.tools.fetch_protocol_docs:main',
			'cbus_decode_packet = cbus.tools.decode_packet:main',
		]
	},
	
	classifiers=[
	
	],
)

