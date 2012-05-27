#!/usr/bin/env python
# staged: "simple" daemon for creating custom scenes listening on lighting GAs
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
`staged` allows you to create simple scenes using INI files that listen for
lighting group address messages and transmits additional messages via cdbusd.

"""

DEFAULT_CONFIG_FILE = '/etc/cbus/staged.ini'

import dbus, gobject
from dbus.mainloop.glib import DBusGMainLoop
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
from cbus.daemon.cdbusd import DBUS_INTERFACE, DBUS_SERVICE, DBUS_PATH


bus = dbus.SystemBus()
obj = bus.get_object(DBUS_SERVICE, DBUS_PATH)
api = dbus.Interface(obj, DBUS_INTERFACE)

def on_lighting_group_on(source_addr, group_addr):
	print "on_lighting_group_on: %r, %r" % (source_addr, group_addr)

def on_lighting_group_off(source_addr, group_addr):
	print "on_lighting_group_off: %r, %r" % (source_addr, group_addr)

def on_lighting_group_ramp(source_addr, group_addr, duration, level):
	print "on_lighting_group_ramp: %r, %r, %r, %r" % (source_addr, group_addr, duration, level)


for n, m in (
	('on_lighting_group_on', on_lighting_group_on),
	('on_lighting_group_off', on_lighting_group_off),
	('on_lighting_group_ramp', on_lighting_group_ramp)
):
	bus.add_signal_receiver(
		m,
		dbus_interface=DBUS_INTERFACE,
		bus_name=DBUS_SERVICE,
		path=DBUS_PATH,
		signal_name=n
	)

loop = gobject.MainLoop()
loop.run()

