#!/usr/bin/env python

from setuptools import setup, find_packages
from platform import system
system = system().lower()

deps = [
		'configparser_plus (>=1.0)',
		'serial (>=2.6)',
		'lxml (>=2.3.2)',
		'Twisted (>=12.0.0)',
]

if system != 'windows':
	# Windows doesn't support some of these things so we run it in reduced
	# functionality mode.
	deps += [
		'daemon (>=1.0)',
		'dbus (>=1.1.1)',
		'pygobject (>=2.28.6)'
	]


setup(
	name="cbus",
	version="0.1",
	description="Library and applications to interact with Clipsal CBus in Python.",
	author="Michael Farrell",
	author_email="micolous@gmail.com",
	url="https://github.com/micolous/cbus",
	license="LGPL3+",
	requires=deps,
	
	# TODO: add scripts to this.
	packages=find_packages(),
	
	entry_points={
		'console_scripts': [
			'cbz_dump_labels = cbus.toolkit.dump_labels:main',
			'cdbusd = cbus.daemon.cdbusd:main',
			'dbuspcid = cbus.daemon.dbuspcid:main',
			'staged = cbus.daemon.staged:main',
		]
	},
	
	classifiers=[
	
	],
)

