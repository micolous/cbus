#!/usr/bin/env python
"""
cdbus.py - DBus service for controlling CBus.
Copyright 2012 Michael Farrell <micolous+git@gmail.com>

This library is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this library.  If not, see <http://www.gnu.org/licenses/>.
"""
import libcbus
import dbus, dbus.service, dbus.glib, gobject
from optparse import OptionParser

DBUS_INTERFACE = 'au.id.micolous.cbus.CBusInterface'
DBUS_SERVICE = 'au.id.micolous.cbus.CBusService'
DBUS_PATH = '/CBusAPI'

class CBusBackendAPI(dbus.service.Object):	
	def __init__(self, bus, pci, object_path=DBUS_PATH):
		self.pci = pci
		dbus.service.Object.__init__(self, bus, object_path)
		
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='y', out_signature='s')
	def lighting_group_on(self, group_id):
		return self.pci.lighting_group_on(group_id)
		
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='y', out_signature='s')
	def lighting_group_off(self, group_id):
		return self.pci.lighting_group_off(group_id)
		
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='ynd', out_signature='s')
	def lighting_group_ramp(self, group_id, duration, level):
		return self.pci.lighting_group_ramp(group_id, duration, level)
		
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='yyy', out_signature='s')
	def recall(self, unit_addr, param_no, count):
		# TODO: implement return response
		return self.pci.recall(unit_addr, param_no, count)
	
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='yy', out_signature='s')
	def identify(self, unit_addr, attribute):
		# TODO: implement return response
		return self.pci.identify(unit_addr, attribute)
		
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='', out_signature='')
	def nop(self):
		# TODO: fix bugs that need this
		return
	

	

def boot_dbus(pci_addr, daemonise, pid_file):
	bus = dbus.SessionBus()
	name = dbus.service.BusName(DBUS_SERVICE, bus=bus)
	pci = libcbus.CBusPCISerial(pci_addr)
	o = CBusBackendAPI(name, pci)
	
	mainloop = gobject.MainLoop()
	
	if daemonise:
		assert pid_file, 'Running in daemon mode means pid_file must be specified.'
		from daemon import daemonize
		daemonize(pid_file)
	
	gobject.threads_init()
	context = mainloop.get_context()
	
	while True:
		if pci.event_waiting():
			e = pci.get_event()
			try:
				ce = libcbus.CBusEvent(e)
				print str(ce)
			except Exception, ex:
				print "exception %s" % ex
			
			print "%r" % e
		context.iteration(True)

def main_optparse():
	parser = OptionParser(usage='%prog [--daemon] [--pci-device]')
	parser.add_option('-D', '--daemon', action='store_true', dest='daemon', default=False, help='Start as a daemon [default: %default]')
	parser.add_option('-P', '--pid', dest='pid_file', default='/var/run/cdbusd.pid', help='Location to write the PID file.  Only has effect in daemon mode.  [default: %default]')
	parser.add_option('-p', '--pci-device', dest='pci_device', default='/dev/ttyUSB0', help='Location of the PCI device [default: %default]')
	
	option, args = parser.parse_args()
	
	boot_dbus(option.pci_device, option.daemon, option.pid_file)

		
if __name__ == '__main__':
	main_optparse()

