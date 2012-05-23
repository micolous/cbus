#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
	name="cbus",
	version="0.1",
	description="Library and applications to interact with Clipsal CBus in Python.",
	author="Michael Farrell",
	author_email="micolous@gmail.com",
	url="https://github.com/micolous/cbus",
	license="LGPL3+",
	requires=(
		'configparser_plus (>=1.0)',
		'serial (>=2.6)',
		'lxml',
		'Twisted (>=12.0.0)',
		'PyGObject',
		'dbus-python',
		
		# Extra optional dependancies not listed here:
		# cbusbot requires ircasync, from https://github.com/micolous/ircbots
		# cdbusd requires python-dbus; only works on UNIX systems.
	),
	
	
	# TODO: add scripts to this.
	packages=find_packages(),
	
	entry_points={
		'console_scripts': [
			'cbz_dump_labels = cbus.toolkit.dump_labels:main',
			'cdbusd = cbus.daemon.cdbusd:main',
		]
	},
	
	classifiers=[
	
	],
)

