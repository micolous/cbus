#!/usr/bin/env python
import struct
from serial import Serial

END_COMMAND = '\r\n'

# command types
POINT_TO_MULTIPOINT = '~\\05'

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

def cbus_checksum(input):
	"Calculates the checksum of a C-Bus command string."
	if input[0] == '\\':
		input = input[1:]
		
	input = input.decode('base16')
	c = 0
	for x in input:
		c += ord(x)
	
	return ((c % 256) ^ 256) + 1

class CBusPCISerial(object):
	def __init__(self, device):
		self.s = Serial(device, 9600)
		self.reset()

	def reset(self):
		# reset the PCI, enable MMI reports so we know when buttons are pressed.
		# (mmi is actually disabled, 59g vs 79g
		self.write('~~~\r\nA3210038g\r\nA3420002g\r\nA3300059g\r\n')
	
	def write(self, msg):
		print "Message = %r" % msg
		self.s.write(msg)
	
	def lighting_group_on(self, group_id):
		# TODO: Implement checksumming
		self.write(POINT_TO_MULTIPOINT + APP_LIGHTING + ROUTING_NONE + LIGHT_ON + ('%02X' % group_id) + 'g' + END_COMMAND)
	
	def lighting_group_off(self, group_id):
		# TODO: Implement checksumming
		self.write(POINT_TO_MULTIPOINT + APP_LIGHTING + ROUTING_NONE + LIGHT_OFF + ('%02X' % group_id) + 'g' + END_COMMAND)
