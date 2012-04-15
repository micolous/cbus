#!/usr/bin/env python

from distutils.core import setup

setup(
	name="cbus",
	version="0.1",
	description="Library and applications to interact with Clipsal CBus in Python.",
	author="Michael Farrell",
	author_email="micolous@gmail.com",
	url="https://github.com/micolous/cbus",
	requires=(
		'configparser_plus (>=1.0)',
		'serial (>=2.6)',
		
		# Extra optional dependancies not listed here:
		# cbusbot requires ircasync, from https://github.com/micolous/ircbots
		# cdbusd requires python-dbus; only works on UNIX systems.
	),
	
	
	# TODO: add scripts to this.
	packages=['libcbus'],
	scripts=[
		'scripts/cdbusd.py',
		'scripts/cbusbot.py'
	]
)

