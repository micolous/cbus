#!/usr/bin/env python
"""
libcbus.py
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
from serial import Serial
from base64 import b16encode, b16decode

HEX_CHARS = "0123456789ABCDEF"

END_COMMAND = '\r\n'

# command types
POINT_TO_MULTIPOINT = '\\05'

# Applications
APP_LIGHTING = '38'

# Routing buffer
ROUTING_NONE = '00'

LIGHT_ON = '79'
LIGHT_OFF = '01'
# light on
#\0538007964 (GA 100)

# light off
#\0538000164 (GA 100)

# set to level
#\053800rr64FF (GA 100, to level 100%/0xff)

RAMP_RATES = {
	'02': 0,
	'0A': 4,
	'12': 8,
	'1A': 12,
	'22': 20,
	'2A': 30,
	'32': 40,
	'3A': 60,
	'42': 90,
	'4A': 120,
	'52': 180,
	'5A': 300,
	'62': 420,
	'6A': 600,
	'72': 900,
	'7A': 1020
}


def duration_to_ramp_rate(seconds):
	if seconds == 0:
		return '02'
	elif seconds <= 4:
		return '0A'
	elif seconds <= 8:
		return '12'
	elif seconds <= 12:
		return '1A'
	elif seconds <= 20:
		return '22'
	elif seconds <= 30:
		return '2A'
	elif seconds <= 40:
		return '32'
	elif seconds <= 60:
		return '3A'
	elif seconds <= 90:
		return '42'
	elif seconds <= 120:
		return '4A'
	elif seconds <= 180:
		return '52'
	elif seconds <= 300:
		return '5A'
	elif seconds <= 420:
		return '62'
	elif seconds <= 600:
		return '6A'
	elif seconds <= 900:
		return '72'
	elif seconds <= 1020:
		return '7A'
	raise OutOfRangeException, 'That duration is too long'

def ramp_rate_to_duration(rate):
	assert len(rate) == 2, "Ramp rate must be two characters."
	rate = rate.upper()	
	return RAMP_RATES[rate]

def cbus_checksum(i):
	"Calculates the checksum of a C-Bus command string."
	if i[0] == '\\':
		i = i[1:]
		
	i = b16decode(i)
	c = 0
	for x in i:
		c += ord(x)
	
	return ((c % 0x100) ^ 0xff) + 1

def add_cbus_checksum(i):
	c = cbus_checksum(i)
	return '%s%02X' % (i, c)

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
			self.application_address = ord(event_bytes[1])
			
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
class CBusPCISerial(object):
	def __init__(self, device):
		self.s = Serial(device, 9600, timeout=1)
		self.reset()

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
	
	def write(self, msg):
		print "Message = %r" % msg
		self.s.write(msg)
	
	def lighting_group_on(self, group_id):
		d = POINT_TO_MULTIPOINT + APP_LIGHTING + ROUTING_NONE + LIGHT_ON + ('%02X' % group_id)
		print "d = %r" % d
		self.write(add_cbus_checksum(d) + 'g' + END_COMMAND)
	
	def lighting_group_off(self, group_id):
		d = POINT_TO_MULTIPOINT + APP_LIGHTING + ROUTING_NONE + LIGHT_OFF + ('%02X' % group_id)
		print "d = %r" % d
		self.write(add_cbus_checksum(d) + 'g' + END_COMMAND)
		
	def event_waiting(self):
		return self.s.inWaiting() >= 1
	
	def get_event(self):
		line = self.s.readline()
		return line

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

