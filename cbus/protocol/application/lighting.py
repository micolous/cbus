#!/usr/bin/env python
# cbus/protocol/application/lighting.py - Lighting Application
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

from cbus.common import *

__all__ = [
	'LightingApplication'
]


class LightingSAL(object):
	def __init__(self, packet=None, group_address=None):
		self.packet = packet
		self.group_address = group_address
	
	@classmethod
	def decode(cls, data, packet):
	
		output = []
		
		while data:
			# parse the data
			command_code = ord(data[0])
			group_address = ord(data[1])
			data = data[2:]
			
			sal, data = SAL_HANDLERS[command_code].decode(data, packet, command_code, group_address)
			
			# gobble it
			# TODO: implement correctly.
			output.append(sal)
			data = ''
		return output


class LightingRampSAL(LightingSAL):
	def __init__(self, packet, group_address, duration, level):
		super(LightingRampSAL, self).__init__(packet, group_address)
		
		self.duration = duration
		self.level = level

	@classmethod
	def decode(cls, data, packet, command_code, group_address):
		duration = ramp_rate_to_duration(command_code)
		level = ord(data[0]) / 255.
		
		data = data[1:]
		return cls(packet, group_address, duration, level), data
		
class LightingOnSAL(LightingSAL):
	def __init__(self, packet, group_address):
		super(LightingOnSAL, self).__init__(packet, group_address)
	
	@classmethod
	def decode(cls, data, packet, command_code, group_address):
		assert command_code == LIGHT_ON, "command_code (%r) != LIGHT_ON (%r)" % (command_code, LIGHT_ON)
		return cls(packet, group_address), data
		

class LightingOffSAL(LightingSAL):
	def __init__(self, packet, group_address):
		super(LightingOffSAL, self).__init__(packet, group_address)
	
	@classmethod
	def decode(cls, data, packet, command_code, group_address):
		assert command_code == LIGHT_OFF, "command_code (%r) != LIGHT_OFF (%r)" % (command_code, LIGHT_OFF)
		return cls(packet, group_address), data
		

SAL_HANDLERS = {
	LIGHT_ON: LightingOnSAL,
	LIGHT_OFF: LightingOffSAL,
}

for x in LIGHT_RAMP_RATES.keys():
	assert x not in SAL_HANDLERS, "LightingRampSAL attempted registration of existing command code!"
	SAL_HANDLERS[x] = LightingRampSAL





class LightingApplication(object):

	@classmethod
	def decode_sal(cls, data, packet):
		return LightingSAL.decode(data, packet)
	
