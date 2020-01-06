#!/usr/bin/env python3

from setuptools import setup, find_packages

deps = [
	'serial (==3.4)',
	'lxml (>=2.3.2)',
	'Twisted (>=12.0.0)',
	'six',
	'pydot',
	'paho_mqtt (==1.5.0)'
]

tests_require = ['pytype']

setup(
	name="cbus",
	version="0.2",
	description="Library and applications to interact with Clipsal CBus in Python.",
	author="Michael Farrell",
	author_email="micolous@gmail.com",
	url="https://github.com/micolous/cbus",
	license="LGPL3+",
	requires=deps,
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

