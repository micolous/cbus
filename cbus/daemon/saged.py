#!/usr/bin/env python
# saged.py - Backend for websockets server in sage, a mobile CBus controller.
# Copyright 2012 Michael Farrell <micolous+git@gmail.com>
# 
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

import dbus, gobject
from cbus.twisted_errors import *
from twisted.internet import glib2reactor

# installing the glib2 reactor breaks sphinx autodoc
# this patches around the issue.
try:
	glib2reactor.install()
except ReactorAlreadyInstalledError:
	pass

from cbus.daemon.cdbusd import DBUS_INTERFACE, DBUS_SERVICE, DBUS_PATH
from twisted.internet import reactor
from twisted.python import log 
from autobahn.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS, createWsUrl
from json import loads, dumps
from argparse import ArgumentParser
import sys

class SageProtocol(WebSocketServerProtocol):
	def __init__(self, *args, **kwargs):
		super(SageProtocol, self).__init__(*args, **kwargs)
		
		# now create a connection to the dbus service
		obj = bus.get_object(DBUS_SERVICE, DBUS_PATH)
		self.api = dbus.Interface(obj, DBUS_INTERFACE)
		
	def onMessage(self, msg, binary):
		msg = loads(msg)
		
		cmd = msg[u'cmd']
		args = msg[u'args']
		
		# now try and handle the message
		if cmd == 'lighting_group_on':
			# handle lighting group on
			print "lighting group on %r" % args[0]
			groups = [int(x) for x in args[0]]
			
			self.api.lighting_group_on(groups)
		elif cmd == 'lighting_group_off':
			# handle lighting group off
			print 'lighting group off %r' % args[0]
			groups = [int(x) for x in args[0]]
			
			self.api.lighting_group_off(groups)
			
		elif cmd == 'lighting_group_ramp':
			# handle lighting ramp
			print 'lighting group ramp group=%s, duration=%s, level=%s' % (args[0], args[1], args[2])
			group = int(args[0])
			duration = int(args[1])
			level = float(args[2])
			
			self.api.lighting_group_ramp(group, duration, level)
			
		elif cmd == 'lighting_group_terminate_ramp':
			print 'lighting group terminate ramp group=%s' % args[0]
			group = int(args[0])
			
			self.api.lighting_group_terminate_ramp(group)
		else:
			print 'unknown command: %r' % cmd
		
		print repr(msg)
		
		#self.sendMessage(dumps(msg))
		

def boot(listen_addr='127.0.0.1', port=8080):
	uri = createWsUrl(listen_addr, port)
	factory = WebSocketServerFactory(uri, debug=False)
	factory.protocol = SageProtocol
	listenWS(factory, interface=listen_addr)
	
	reactor.run()

if __name__ == '__main__':
	# do commandline handling
	parser = ArgumentParser(usage='%(prog)s')
	
	#parser.add_argument('-r', '--root-path',
	#	dest='root_path',
	#	default='cbus/sage_root',
	#	help='Root path of the sage webserver.  Used to serve the accompanying javascript and HTML content [default: %(default)s]'
	#)
	
	parser.add_argument('-h', '--listen-addr',
		dest='listen_addr',
		default='127.0.0.1',
		help='IP address to listen the web server on [default: %(default)s]'
	)
	
	parser.add_argument('-p', '--port',
		dest='port',
		type=int,
		default=8080,
		help='Port to run the web server on [default: %(default)s]'
	)
	
	parser.add_argument('-l', '--log',
		dest='log_target',
		type=file,
		default=sys.stdout,
		help='Log target [default: %(default)s]'
	)
	
	option = parser.parse_args()
	
	log.startLogging(option.log_target)
	boot(option.listen_addr, option.port)
