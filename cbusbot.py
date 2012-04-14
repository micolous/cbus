#!/usr/bin/env python
"""
cbusbot: Program to get CBUS events on IRC, and control from IRC.
Copyright 2010 - 2012 Michael Farrell <http://micolous.id.au>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re, asyncore
from datetime import datetime, timedelta
from configparser_plus import ConfigParserPlus
from sys import argv, exit
from ircasync import *
from subprocess import Popen, PIPE
from thread import start_new_thread
from time import sleep
from Queue import Queue, Full
from libcbus import *

DEFAULT_SETTINGS = {
	'cbusbot': {
		'server': 'localhost',
		'port': 6667,
		'nick': 'cbusbot',
		'channel': 'test',
		
		'pcidev': '/dev/ttyUSB0'
	}
}


config = ConfigParserPlus(DEFAULT_SETTINGS)
try:
	config.readfp(open(argv[1]))
except:
	try:
		config.readfp(open('cbusbot.ini'))
	except:
		print "Syntax:"
		print "  %s [config]" % argv[0]
		print ""
		print "If no configuration file is specified or there was an error, it will default to `cbusbot.ini'."
		print "If there was a failure reading the configuration, it will display this message."
		exit(1)

# get version information from git
try: VERSION = config.get('cbusbot', 'version') + '; %s'
except: VERSION = 'cbusbot; https://github.com/micolous/cbus/; %s'
try: VERSION = VERSION % Popen(["git","branch","-v","--contains"], stdout=PIPE).communicate()[0].strip()
except: VERSION = VERSION % 'unknown'
del Popen, PIPE

ON = [
	'on',
	'y',
	'1',
	'enable',
]

OFF = [
	'off',
	'n',
	'0',
	'disable'
]
	

class CBusBot(object):
	def __init__(self, config):
		# setup configuration.
		section = 'cbusbot'
		
		self.server = config.get(section, 'server')
		self.port = config.getint(section, 'port')		
		self.nick = config.get(section, 'nick')
		self.channel = config.get(section, 'channel').lower()
		self.pcidev = config.get(section, 'pcidev')
		
		# setup irc client library.
		self.irc = IRC(nick=self.nick, start_channels=[self.channel], version=VERSION)
		self.irc.bind(self.handle_lighting, PRIVMSG, r'^!cbus (\d+) (\S+)$')
		self.irc.bind(self.handle_welcome, RPL_WELCOME)
		
		self.pci = CBusPCISerial(self.pcidev)
		
	def handle_lighting(self, event, match):
		if event.channel.lower() != self.channel:
			# ignore messages not from our channel.
			return
		
		group_addr = match.group(1)
		
		try:
			group_addr = int(group_addr)
		except:
			print "non-numeric group address"
			return
		
		if group_addr < 0 or group_addr > 255:
			print "group address out of range"
			return
		
		state = match.group(2).lower()
		
		if state in ON:
			# send on command
			self.pci.lighting_group_on(group_addr)
			
		elif state in OFF:
			# send off command
			self.pci.lighting_group_off(group_addr)
		
		elif state.startswith('ramp-'):
			try:
				keys = state.split('-')
			
				if len(keys) == 2:
					level = float(keys[1])
					rate = 12
				elif len(keys) == 3:
					level = float(keys[1])
					rate = int(keys[2])
					
			except:
				print "error parsing ramp request"
				return
			# send ramp command
			self.pci.lighting_group_ramp(group_addr, rate, level)
			
		else:
			print "unknown mode %r" % state
		
		
	
	def handle_welcome(self, event, match):
		# most networks require this usermode be set on bots.
		event.connection.usermode("+B")
		
	def connect(self):
		# spawn event loop
		start_new_thread(self.process_events_loop, ())
		
		self.irc.make_conn(self.server, self.port)
		
	def process_events_loop(self):
		while True:
			try:
				print "line 142"
				if self.pci.event_waiting():
					print "line 144"
					e = self.pci.get_event()
					print "line 146"
					ce = CBusEvent(e)
					print "line 148"
					if ce.event_type != "MMI":
						print "line 150"
						print str(ce)
						print "line 152"
						self.irc.tell(self.channel, str(ce))
				
				print "poke"
				sleep(1)

			except Exception, ex:
				print "exception %s" % ex
			


bot = CBusBot(config)
bot.connect()

# now tell asyncore to pump
asyncore.loop()

