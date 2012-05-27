#!/usr/bin/env python
# dbuspcid: Implements subset of CBus serial API for connecting to cdbusd
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

"""
`fakepci` allows you to create a fake CNI (TCP PCI) or serial PCI that connects
to cdbusd.

"""

import dbus
import gobject
import sys
from optparse import OptionParser
from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)

from cbus.daemon.cdbusd import DBUS_INTERFACE, DBUS_SERVICE, DBUS_PATH
from twisted.internet.protocol import Factory
from cbus.protocol.pciserverprotocol import PCIServerProtocol
import cbus.common
from twisted.python import log
from twisted.internet import reactor


class FakePCI(PCIServerProtocol):
	
	triggers = {}
	
	def __init__(self, bus):
		obj = bus.get_object(DBUS_SERVICE, DBUS_PATH)
		self.api = dbus.Interface(obj, DBUS_INTERFACE)
		
				
		
		# wire event listeners
		for n, m in (
			('on_lighting_group_on', self.lighting_group_on),
			('on_lighting_group_off', self.lighting_group_off),
			('on_lighting_group_ramp', self.lighting_group_ramp),
		):
			bus.add_signal_receiver(
				m,
				dbus_interface=DBUS_INTERFACE,
				bus_name=DBUS_SERVICE,
				path=DBUS_PATH,
				signal_name=n
			)
			
	def on_lighting_group_on(self, group_addr):
		self.api.lighting_group_on(group_addr)
	
	def on_lighting_group_off(self, group_addr):
		self.api.lighting_group_off(group_addr)
	
	def on_lighting_group_ramp(self, group_addr, duration, level):
		self.api.lighting_group_ramp(group_addr, duration, level)
	

class FakePCIFactory(Factory):
	def __init__(self, protocol):
		self.protocol = protocol
		
	def buildProtocol(self, addr):
		return self.protocol


def boot(serial_mode, addr, daemon_enable, pid_file, session_bus=False):
	if daemon_enable:
		raise ValueError, "daemon mode not supported yet"
	
	if session_bus:
		bus = dbus.SessionBus()
	else:
		bus = dbus.SystemBus()
	
	
	fakepci = FakePCI(bus)
	
	if serial_mode:
		raise ValueError, 'serial mode not implemented'
	else:
		# tcp mode
		reactor.listenTCP(int(addr), FakePCIFactory(fakepci))
		
		
	
	

def main():
	parser = OptionParser(usage='%prog')
	parser.add_option('-D', '--daemon',  action='store_true', dest='daemon', default=False, help='Start as a daemon [default: %default]')
	parser.add_option('-P', '--pid', dest='pid_file', default='/var/run/cdbusd.pid', help='Location to write the PID file.  Only has effect in daemon mode.  [default: %default]')
	parser.add_option('-s', '--serial-pci', dest='serial_pci', default=None, help='Serial port to listen on.  Either this or -t must be specified.')
	parser.add_option('-t', '--tcp-pci', dest='tcp_pci', default=None, help='TCP port to listen on (CNI).  Either this or -s must be specified.')
	parser.add_option('-S', '--session-bus', action='store_true', dest='session_bus', default=False, help='Bind to the session bus instead of the system bus [default: %default]')
	parser.add_option('-l', '--log-file', dest='log', default=None, help='Destination to write logs [default: stdout]')
	
	options, args = parser.parse_args()
	
	if options.serial_pci and options.tcp_pci:
		parser.error('Both serial and TCP CBus PCI listen addresses were specified!  Use only one...')
	elif options.serial_pci:
		serial_mode = True
		addr = options.serial_pci
	elif options.tcp_pci:
		serial_mode = False
		addr = options.tcp_pci
	else:
		parser.error('No CBus PCI listen address was specified!  (See -s or -t option)')
		
	if options.log:
		log.startLogging(options.log)
	else:
		log.startLogging(sys.stdout)
	
	a = [options.daemon, options.pid_file, options.session_bus]
	
	reactor.callWhenRunning(boot, serial_mode, addr, options.daemon, options.pid_file, options.session_bus)
	reactor.run()

if __name__ == '__main__':
	main()

	
	
