#!/usr/bin/env python
"""
libcbus/common.py - Constants and common functions used in the CBUS protocol.
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


HEX_CHARS = "0123456789ABCDEF"

END_COMMAND = '\r\n'

# command types
POINT_TO_MULTIPOINT = '\\05'
POINT_TO_POINT = '\\06'
# undocumented command type issued for status inquiries by toolkit?
POINT_TO_46 = '\\46'

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

MIN_RAMP_RATE = 0
MAX_RAMP_RATE = 1020

RECALL = '1A'
IDENTIFY = '21'

# these are valid confirmation codes used in acknowledge events.
CONFIRMATION_CODES = 'hijklmnopqrstuvwxyzGHIJKLMNOPQRSTUVWXYZ'

MIN_GROUP_ADDR = 0
MAX_GROUP_ADDR = 255

def duration_to_ramp_rate(seconds):
	for k, v in RAMP_RATES.iteritems():
		if seconds <= v:
			return k
	raise ValueError, 'That duration is too long!'

def ramp_rate_to_duration(rate):
	assert len(rate) == 2, "Ramp rate must be two characters."
	rate = rate.upper()	
	return RAMP_RATES[rate]

def cbus_checksum(i):
	"""
	Calculates the checksum of a C-Bus command string.
	
	Fun fact: C-Bus toolkit and C-Gate do not use commands with checksums.
	"""
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


