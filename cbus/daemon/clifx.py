#!/usr/bin/env python
# clifx.py - Bridges C-Bus lighting events to a LIFX bulb
# Copyright 2012-2014 Michael Farrell <micolous+git@gmail.com>
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


from cbus.twisted_errors import *
from cbus.daemon.cdbusd import DBUS_INTERFACE, DBUS_SERVICE, DBUS_PATH
from twisted.internet import reactor, defer
from twisted.python import log
from zope.interface import implements
from txdbus import client
from argparse import ArgumentParser
import sys, pylifx


class DBusRemoteWrapperMethod(object):
	"""
	Wrapper for methods for interface.callRemote
	"""
	def __init__(self, obj, methname):
		self._obj = obj
		self._methname = methname

	def __call__(self, *args, **kwargs):
		return self._obj.callRemote(self._methname, *args, **kwargs)


class DBusRemoteWrapper(object):
	"""
	Wrapper for interfaces that makes everything a callRemote.
	"""
	def __init__(self, obj):
		self._obj = obj

	def __getattr__(self, name):
		return DBusRemoteWrapperMethod(self._obj, name)


class LifxProtocol(object):
	def __init__(self, *args, **kwargs):
		self.api = kwargs.pop('api')
		self.lifx_connection = kwargs.pop('lifx_connection')


	def on_lighting_group_on(self, source_addr, group_addr):
		self.lifx_connection.on()
		
	def on_lighting_group_off(self, source_addr, group_addr):
		self.lifx_connection.off()
	
	def on_lighting_group_ramp(self, source_addr, group_addr, duration, level):
		pass


@defer.inlineCallbacks
def boot(session_bus=False, lifx_mac=None, group_addr=None, interface=None):
	global api
	global factory
	lifx_connection = pylifx.LifxController(lifx_mac, intf_name=interface)
	
	conn = yield client.connect(reactor, 'session' if session_bus else 'system')
	obj = yield conn.getRemoteObject(DBUS_SERVICE, DBUS_PATH)
	api = DBusRemoteWrapper(obj)

	uri = createWsUrl(listen_addr, port)
	factory = LifxProtocol(api=api, lifx_connection=lifx_connection)

	# register signals
	for n, m in (
		('on_lighting_group_on', factory.on_lighting_group_on),
		('on_lighting_group_off', factory.on_lighting_group_off),
		('on_lighting_group_ramp', factory.on_lighting_group_ramp)
	):
		obj.notifyOnSignal(n, m)



if __name__ == '__main__':
	# do commandline handling
	parser = ArgumentParser(usage='%(prog)s')
	
	parser.add_argument('-l', '--log',
		dest='log_target',
		type=file,
		default=sys.stdout,
		help='Log target [default: stdout]'
	)
	
	parser.add_argument('-S', '--session-bus',
		action='store_true',
		dest='session_bus',
		default=False,
		help='Bind to the session bus instead of the system bus [default: %(default)s]'
	)
	
	parser.add_argument('-m', '--lifx-mac',
		dest='lifx_mac',
		required=True,
		help='MAC address of the LIFX bridge bulb'
	)
	
	parser.add_argument('-g', '--group-addr',
		dest='group_addr',
		type=int,
		required=True,
		help='Group address to listen for on the CBus network'
	)
	parser.add_argument('-i', '--iface',
		dest='interface',
		required=False,
		help='Network interface to use to broadcast LIFX packets'
	)

	option = parser.parse_args()

	log.startLogging(option.log_target)

	reactor.callWhenRunning(boot, option.session_bus, option.lifx_mac, option.group_addr, option.interface)
	reactor.run()	
