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
import dbus, dbus.service, dbus.glib, gobject, libcbus

DBUS_INTERFACE = 'au.id.micolous.cbus.CBusInterface'
DBUS_SERVICE = 'au.id.micolous.cbus.CBusService'
DBUS_PATH = '/CBusAPI'

class CBusBackendAPI(dbus.service.Object):	
	def __init__(self, bus, pci, object_path=DBUS_PATH):
		self.pci = pci
		dbus.service.Object.__init__(self, bus, object_path)
		
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='y', out_signature='')
	def lighting_group_on(self, group_id):
		self.pci.lighting_group_on(group_id)
		
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='y', out_signature='')
	def lighting_group_off(self, group_id):
		self.pci.lighting_group_off(group_id)
		
	@dbus.service.method(dbus_interface=DBUS_INTERFACE, in_signature='ynd', out_signature='')
	def lighting_group_ramp(self, group_id, duration, level):
		self.pci.lighting_group_ramp(group_id, duration, level)

def setup_dbus():
	#bus = dbus.SystemnBus()
	bus = dbus.SessionBus()
	name = dbus.service.BusName(DBUS_SERVICE, bus=bus)
	pci = libcbus.CBusPCISerial('/dev/ttyUSB1')
	o = CBusBackendAPI(name, pci)
	return o

def boot_dbus():
	mainloop = gobject.MainLoop()
	mainloop.run()

if __name__ == '__main__':
	setup_dbus()
	boot_dbus()

