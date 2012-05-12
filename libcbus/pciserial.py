#!/usr/bin/env python
"""
libcbus/pciserial.py - Serial / USB interface to the CBus PCI (5500PC/5500PCU)
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
from serial import serial_for_url
from libcbus.pci import CBusPCI

class CBusPCISerial(CBusPCI):
	"""
	Serial (RS232) / USB CBus PCI module.
	
	"""

	def __init__(self, uri):
		self.s = serial_for_url(uri, 9600, timeout=1)
		super(CBusPCISerial, self).__init__()
		
	def write(self, msg):
		print "Message = %r" % msg
		self.s.write(msg)
	
	def event_waiting(self):
		return self.s.inWaiting() >= 1
	
	def get_event(self):
		line = self.s.readline()
		return line
