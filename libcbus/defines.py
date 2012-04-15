#!/usr/bin/env python
"""
libcbus/defines.py - Constants used in the CBUS protocol.
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

RECALL = '1A'
IDENTIFY = '21'

# these are valid confirmation codes used in acknowledge events.
CONFIRMATION_CODES = 'hijklmnopqrstuvwxyzGHIJKLMNOPQRSTUVWXYZ'