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
import warnings

__all__ = [
	'LightingApplication',
	'LightingSAL',
	'LightingRampSAL',
	'LightingOnSAL',
	'LightingOffSAL',
	'LightingTerminateRampSAL',
]


class LightingSAL(object):
	"""
	Base type for lighting application SALs.
	"""
	def __init__(self, packet=None, group_address=None):
		"""
		This should not be called directly by your code!
		
		Use one of the subclasses of cbus.protocol.lighting.LightingSAL instead.
		"""
		self.packet = packet
		self.group_address = group_address
		
		assert packet != None, 'packet must not be none.'
		
		if self.packet.application == None:
			# no application set on the packet, set it.
			self.packet.application = APP_LIGHTING
		elif self.packet.application != APP_LIGHTING:
			raise ValueError, 'packet has a different application set already. cannot have multiple application SAL in the same packet.'
	
	@classmethod
	def decode(cls, data, packet):
		"""
		Decodes a lighting application packet and returns it's SAL(s).
		
		:param data: SAL data to be parsed.
		:type data: str
		
		:param packet: The packet that this data is associated with.
		:type packet: cbus.protocol.base_packet.BasePacket
		
		:returns: The SAL messages contained within the given data.
		:rtype: list of cbus.protocol.application.lighting.LightingSAL
		
		"""
		output = []
		
		while data:
			# parse the data
			
			if len(data) < 2:
				# not enough data to go on.
				warnings.warn("Got 1 byte of stray SAL for lighting application (malformed packet)", UserWarning)
				break
			
			command_code = ord(data[0])
			group_address = ord(data[1])
			data = data[2:]
			
			if command_code not in SAL_HANDLERS:
				warnings.warn('Got unknown lighting command %r, stopping processing prematurely' % command_code, UserWarning)
				break
				
			sal, data = SAL_HANDLERS[command_code].decode(data, packet, command_code, group_address)
		
			if sal:
				output.append(sal)
		return output
	
	def encode(self):
		"""
		Encodes the SAL into a format for sending over the C-Bus network.
		"""
		if not validate_ga(self.group_address):
			raise ValueError, 'group_addr out of range (%d - %d), got %r' % (MIN_GROUP_ADDR, MAX_GROUP_ADDR, self.group_address)
		
		return []


class LightingRampSAL(LightingSAL):
	"""
	Lighting Ramp (fade) event SAL
	
	Instructs the given group address to fade to a lighting level (brightness)
	over a given duration.
	
	"""
	def __init__(self, packet, group_address, duration, level):
		"""
		Creates a new SAL Lighting Ramp message.
		
		:param packet: The packet that this SAL is to be included in.
		:type packet: cbus.protocol.base_packet.BasePacket
		
		:param group_address: The group address to ramp.
		:type group_address: int
		
		:param duration: The duration to ramp over, in seconds.
		:type duration: int
		
		:param level: The level to ramp to, with 0.0 indicating off, and 1.0 indicating full brightness.
		:type level: float
		"""
		super(LightingRampSAL, self).__init__(packet, group_address)
		
		self.duration = duration
		self.level = level

	@classmethod
	def decode(cls, data, packet, command_code, group_address):
		"""
		Do not call this method directly -- use LightingSAL.decode
		"""
		duration = ramp_rate_to_duration(command_code)
		
		if not data:
			warnings.warn('Couldn\'t get level for LightingRampSAL, no more data.', UserWarning)
			return None
			
		level = ord(data[0]) / 255.
		
		data = data[1:]
		return cls(packet, group_address, duration, level), data
	
	def encode(self):
		if not (0.0 <= self.level <= 1.0):
			raise ValueError, 'Ramp level is out of bounds.  Must be between 0.0 and 1.0 (got %r).' % self.level
		
		if not validate_ramp_rate(self.duration):
			raise ValueError, 'Duration is out of bounds, must be between %d and %d (got %r)' % (MIN_RAMP_RATE, MAX_RAMP_RATE, self.duration)
			
		return super(LightingRampSAL, self).encode() + [
			duration_to_ramp_rate(self.duration),
			self.group_address,
			int(self.level * 255)
		]
		
class LightingOnSAL(LightingSAL):
	"""
	Lighting on event SAL
	
	Instructs a given group address to turn it's load on.
	"""
	def __init__(self, packet, group_address):
		"""
		Creates a new SAL Lighting On message.
		
		:param packet: The packet that this SAL is to be included in.
		:type packet: cbus.protocol.base_packet.BasePacket
		
		:param group_address: The group address to turn on.
		:type group_address: int
		
		"""
		super(LightingOnSAL, self).__init__(packet, group_address)
	
	@classmethod
	def decode(cls, data, packet, command_code, group_address):
		"""
		Do not call this method directly -- use LightingSAL.decode
		"""
		assert command_code == LIGHT_ON, "command_code (%r) != LIGHT_ON (%r)" % (command_code, LIGHT_ON)
		return cls(packet, group_address), data
		
	def encode(self):
		return super(LightingOnSAL, self).encode() + [
			LIGHT_ON,
			self.group_address
		]

class LightingOffSAL(LightingSAL):
	"""
	Lighting off event SAL
	
	Instructs a given group address to turn it's load off.
	"""
	def __init__(self, packet, group_address):
		"""
		Creates a new SAL Lighting Off message.
		
		:param packet: The packet that this SAL is to be included in.
		:type packet: cbus.protocol.base_packet.BasePacket
		
		:param group_address: The group address to turn off.
		:type group_address: int
		
		"""
		super(LightingOffSAL, self).__init__(packet, group_address)
	
	@classmethod
	def decode(cls, data, packet, command_code, group_address):
		"""
		Do not call this method directly -- use LightingSAL.decode
		"""
		assert command_code == LIGHT_OFF, "command_code (%r) != LIGHT_OFF (%r)" % (command_code, LIGHT_OFF)
		return cls(packet, group_address), data
		
	def encode(self):
		return super(LightingOffSAL, self).encode() + [
			LIGHT_OFF,
			self.group_address
		]

class LightingTerminateRampSAL(LightingSAL):
	"""
	Lighting terminate ramp event SAL
	
	Instructs the given group address to discontinue any ramp operations in
	progress, and use the brightness that they are currently at.
	"""
	def __init__(self, packet, group_address):
		"""
		Creates a new SAL Lighting Terminate Ramp message.
		
		:param packet: The packet that this SAL is to be included in.
		:type packet: cbus.protocol.base_packet.BasePacket
		
		:param group_address: The group address to stop ramping.
		:type group_address: int
		
		"""
		super(LightingTerminateRampSAL, self).__init__(packet, group_address)
	
	@classmethod
	def decode(cls, data, packet, command_code, group_address):
		"""
		Do not call this method directly -- use LightingSAL.decode
		"""
		assert command_code == LIGHT_TERMINATE_RAMP, "command_code (%r) != LIGHT_TERMINATE_RAMP (%r)" % (command_code, LIGHT_TERMINATE_RAMP)
		return cls(packet, group_address), data
		
	def encode(self):
		return super(LightingTerminateRampSAL, self).encode() + [
			LIGHT_TERMINATE_RAMP,
			self.group_address
		]


# register SAL handlers (used by LightingSAL to map commands)
SAL_HANDLERS = {
	LIGHT_ON: LightingOnSAL,
	LIGHT_OFF: LightingOffSAL,
	LIGHT_TERMINATE_RAMP: LightingTerminateRampSAL,
}

for x in LIGHT_RAMP_RATES.keys():
	assert x not in SAL_HANDLERS, "LightingRampSAL attempted registration of existing command code!"
	SAL_HANDLERS[x] = LightingRampSAL


class LightingApplication(object):
	"""
	This class is called in the cbus.protocol.applications.APPLICATIONS dict in
	order to describe how to decode lighting application events recieved from
	the network.
	
	Do not call this class directly.
	"""
	@classmethod
	def decode_sal(cls, data, packet):
		"""
		Decodes a lighting application packet and returns it's SAL(s).
		"""
		return LightingSAL.decode(data, packet)

