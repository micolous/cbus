#!/usr/bin/env python
"""
libcbus/pci.py - Base CBus PCI protocol library.
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

import struct
from base64 import b16encode, b16decode
from libcbus.base import *
from libcbus.common import *

class CBusEvent(object):
	def __init__(self, event_string):
		" decode the given event string "
		event_string = event_string.strip()
		self.event_string = event_string
		
		for x in self.event_string:
			if x not in HEX_CHARS:
				raise Exception, "Not supported yet: %r" % self.event_string
		
		# decode string
		event_bytes = b16decode(self.event_string)
		
		event_code = ord(event_bytes[0])
		
		if event_code >= 0xC0:
			# this is an MMI of length [0] - C0 (quick start page 13)
			self.event_length = ord(event_bytes[0]) - 0xC0
			self.event_type = 'MMI'
			self.application = ord(event_bytes[1])
			
			# TODO: Implement this.
		elif event_code == 0x05:
			# this is a point-to-multipoint message.
			self.event_type = 'PTMP'
			self.source_address = ord(event_bytes[1])
			self.application = ord(event_bytes[2])
			self.routing = ord(event_bytes[3])
			
			if event_string[4:6] == APP_LIGHTING:
				# lighting application
				self.application_type = 'LIGHTING'
				self.lighting_event = event_string[8:10]
				if self.lighting_event in RAMP_RATES.keys():
					# ramp
					self.lighting_event_type = 'RAMP'
					self.lighting_ramp_rate = ramp_rate_to_duration(self.lighting_event)
				elif self.lighting_event == LIGHT_ON:
					self.lighting_event_type = 'ON'
				elif self.lighting_event == LIGHT_OFF:
					self.lighting_event_type = 'OFF'
				
				self.group_address = ord(event_bytes[5])
				self.checksum = ord(event_bytes[6])
			else:
				# not implemented.
				raise Exception, "not implemented application %r" % (event_string[4:6])

	def __str__(self):
		if self.event_type == 'PTMP' and self.application_type == 'LIGHTING':
			if self.lighting_event_type == 'RAMP':
				ramp = ', rate=%d' % self.lighting_ramp_rate
			else:
				ramp = ''
				
			return '<PTMP src=%d, app=%s, routing=%d, group=%d, action=%s%s>' % (
				self.source_address, self.application_type, self.routing,
				self.group_address, self.lighting_event_type, ramp
			)
		else:
			return '???'


class CBusPCI(CBusBase):
	"""
	Generic CBusPCI module.
	
	You should subclass this to implement a libcbus implementation that talks
	over CBus serial protocol (includes USB and CNI).
	
	"""
	def __init__(self):
		self.reset()
		
		self.next_confirmation_index = 0
	
	def get_confirmation_code(self):
		"""
		Creates a confirmation code, and increments forward the next in the list.
		
		"""
		o = CONFIRMATION_CODES[self.next_confirmation_index]
		
		self.next_confirmation_index += 1
		self.next_confirmation_index %= len(CONFIRMATION_CODES)
		
		return o
	
	def write(self, msg):
		raise NotImplementedError, "CBusPCI.write not implemented.  Use subclass (eg: CBusPCISerial)."

	def reset(self):
		# reset the PCI, disable MMI reports so we know when buttons are pressed.
		# (mmi toggle is 59g disable vs 79g enable)
		# 
		# MMI calls aren't needed to get events from light switches and other device on the network.
		
		# full system reset
		self.write('~~~\r\n')
		
		# serial user interface guide sect 10.2
		# Set application address 1 to 38 (lighting)
		self.write('A3210038g\r\n')
		
		# Interface options #3 set to 02
		# "Reserved".
		self.write('A3420002g\r\n')
		
		# Interface options #1
		# = 0x59 / 0101 1001
		# 0: CONNECT
		# 3: SRCHK - strict checksum check
		# 4: SMART
		# 5: MONITOR
		# 6: IDMON
		self.write('A3300059g\r\n')
		
		
		
		# quick start guide version
		#self.write('~~~\r\nA3210038g\r\nA3420002g\r\nA3300059g\r\n')
	
	
	def lighting_group_on(self, group_id):
		super(CBusPCI, self).lighting_group_on(group_id)
	
		d = POINT_TO_MULTIPOINT + APP_LIGHTING + ROUTING_NONE + LIGHT_ON + ('%02X' % group_id)
		conf = self.get_confirmation_code()
		#print "d = %r" % d
		self.write(add_cbus_checksum(d) + conf + END_COMMAND)
		
		return conf
	
	def lighting_group_off(self, group_id):
		super(CBusPCI, self).lighting_group_off(group_id)
	
		d = POINT_TO_MULTIPOINT + APP_LIGHTING + ROUTING_NONE + LIGHT_OFF + ('%02X' % group_id)
		#print "d = %r" % d
		conf = self.get_confirmation_code()
		self.write(add_cbus_checksum(d) + conf + END_COMMAND)
		return conf
	
	def lighting_group_ramp(self, group_id, duration, level=1.0):
		super(CBusPCI, self).lighting_group_ramp(group_id, duration, level)
		
		level = int(level * 255)
		d = POINT_TO_MULTIPOINT + APP_LIGHTING + ROUTING_NONE + LIGHT_OFF + duration_to_ramp_rate(duration) + ('%02X%02X' % (group_id, level))
		conf = self.get_confirmation_code()
		self.write(add_cbus_checksum(d) + conf + END_COMMAND)
		return conf
		
		
	def recall(self, unit_addr, param_no, count):
		super(CBusPCI, self).recall(unit_addr, param_no, count)
		d = '%s%02X%s%s%02X%02X' % (POINT_TO_46, unit_addr, ROUTING_NONE, RECALL, param_no, count)
		conf = self.get_confirmation_code()
		self.write(add_cbus_checksum(d) + conf + END_COMMAND)
		return conf
	
	def identify(self, unit_addr, attribute):
		super(CBusPCI, self).identify(unit_addr, attribute)
		d = '%s%02X%s%s%02X' % (POINT_TO_46, unit_addr, ROUTING_NONE, RECALL, attribute)
		conf = self.get_confirmation_code()
		self.write(add_cbus_checksum(d) + conf + END_COMMAND)
		return conf

def event_test(port):
	s = CBusPCISerial(port)
	while True:
		e = s.get_event();
		try:
			ce = CBusEvent(e)
			print str(ce)
		except Exception, ex:
			print "exception %s" % ex
			
		print "%r" % e

