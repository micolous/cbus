#!/usr/bin/env python
import struct
from serial import Serial

# command types
POINT_TO_MULTIPOINT = '\\05'

# Applications
APP_LIGHTING = '38'

# Routing buffer
ROUTING_NONE = '00'


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
	elif seconds 


class CBusPCISerial(object):
	def __init__(self, device):
		self.s = Serial(device, 9600)
		self.reset()

	def reset(self):
		# reset the PCI
		self.s.write('~')
	
	

