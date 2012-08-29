#!/usr/bin/env python
# cbus/protocol/application/clock.py - Clock and Timekeeping Application
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
from struct import unpack, pack
from datetime import date, time
import warnings

__all__ = [
	'ClockApplication',
	'ClockSAL',
	'ClockUpdateSAL',
	'ClockRequestSAL',
]


class ClockSAL(object):
	"""
	Base type for clock and timekeeping application SALs.
	"""
	def __init__(self, packet=None):
		"""
		This should not be called directly by your code!
		
		Use one of the subclasses of cbus.protocol.clock.ClockSAL instead.
		"""
		self.packet = packet
		
		assert packet != None, 'packet must not be none.'
		
		if self.packet.application == None:
			# no application set on the packet, set it.
			self.packet.application = APP_CLOCK
		elif self.packet.application != APP_CLOCK:
			raise ValueError, 'packet has a different application set already. cannot have multiple application SAL in the same packet.'
	
	@classmethod
	def decode(cls, data, packet):
		"""
		Decodes a clock broadcast application packet and returns it's SAL(s).
		
		:param data: SAL data to be parsed.
		:type data: str
		
		:param packet: The packet that this data is associated with.
		:type packet: cbus.protocol.base_packet.BasePacket
		
		:returns: The SAL messages contained within the given data.
		:rtype: list of cbus.protocol.application.clock.ClockSAL
		
		"""
		output = []
		
		while data:
			# parse the data
			command_code = ord(data[0])
			data = data[1:]
			
			#if command_code not in SAL_HANDLERS:
			if (command_code & 0x80) == 0x80:
				warnings.warn('Got unknown clock command %02x; long form is not used.' % command_code, UserWarning)
				break
				
			if (command_code & 0xE0) != 0:
				warnings.warn('Got unknown clock command %02x; don\'t know how to process the other bits.' % command_code, UserWarning)
				break
			
			if (command_code & 0x08) == 0x08:
				# "update network variable"
				sal, data = ClockUpdateSAL.decode(data, packet, command_code)
			elif (command_code & 0x1F) == 0x11:
				# "request refresh"
				sal, data = ClockRequestSAL.decode(data, packet, command_code)
			else:
				# unknown
				warnings.warn('Got unknown clock command %02x; last stage dropout' % command_code, UserWarning)
				break
		
			if sal:
				output.append(sal)
		return output
	
	def encode(self):
		"""
		Encodes the SAL into a format for sending over the C-Bus network.
		"""
		#if not validate_ga(self.group_address):
		#	raise ValueError, 'group_addr out of range (%d - %d), got %r' % (MIN_GROUP_ADDR, MAX_GROUP_ADDR, self.group_address)
		
		return []


class ClockUpdateSAL(ClockSAL):
	"""
	Clock update event SAL.
	
	Informs the network of the current time.
	
	"""
	
	@property
	def is_date(self):
		return self.variable == 2
	
	@property
	def is_time(self):
		return self.variable == 1
	
	def __init__(self, packet, variable, val):
		"""
		Creates a new SAL Clock update message.
		
		:param packet: The packet that this SAL is to be included in.
		:type packet: cbus.protocol.base_packet.BasePacket
		
		:param variable: The variable being updated.  
		:type variable: int
		
		:param val: The value of that variable.  Dates are represented in native date format, and times are represented in native time format.
		:type val: date or time
		
		"""
		super(ClockUpdateSAL, self).__init__(packet)
		self.variable = variable
		self.val = val

	@classmethod
	def decode(cls, data, packet, command_code):
		"""
		Do not call this method directly -- use ClockSAL.decode
		"""
		
		variable = ord(data[0])
		data_length = command_code & 0x07
		val = data[1:data_length]
		data = data[data_length:]
		
		if variable == 0x02:
			# date (23.5.1.2)
			# length must be 0x06
			if data_length != 0x06:
				warnings.warn('Date variable being sent with length != 5 (got %d instead)' % data_length, UserWarning)
				return None, data
			
			# now decode the date
			year, month, day, dow = unpack('>HBBB', val)
			# note: dow / day of week is ignored
			
			return cls(packet, variable, date(year, month, day)), data
		
		elif variable == 0x01:
			# time (23.5.1.1)
			# length must be 0x05
			if data_length != 0x05:
				warnings.warn('Time variable being sent with length != 4 (got %d instead)' % data_length, UserWarning)
				return None, data
			
			# now decode the time
			hour, minute, second, dst = unpack('>BBBB', val)
			# note: dst / daylight savings flag is ignored
			
			return cls(packet, variable, time(hour, minute, second)), data
		else:
			warnings.warn('Tried to decode unknown clock update variable %02x' % variable, UserWarning)
			# attempt to skip the bad data and recover
			return None, data[data_length:]
	
	def encode(self):
		if self.variable == 0x01:
			# time
			# TODO: implement DST flag
			val = pack('>BBBB', self.val.hour, self.val.minute, self.val.second, 255)
		elif self.variable == 0x02:
			# date
			val = pack('>HBBB', self.val.year, self.val.month, self.val.day, self.val.weekday())
		else:
			# unknown
			raise ValueError, "Don't know how to pack network variable %02x" % self.variable
		
		return super(ClockUpdateSAL, self).encode() + [
			0x08 | (len(val) + 1),
			self.variable,
		] + [ord(x) for x in val]


class ClockRequestSAL(ClockSAL):
	"""
	Clock request event SAL.
	
	Requests network time.
	
	"""
	
	def __init__(self, packet):
		"""
		Creates a new SAL Clock request message.
		
		:param packet: The packet that this SAL is to be included in.
		:type packet: cbus.protocol.base_packet.BasePacket
		
		"""
		super(ClockRequestSAL, self).__init__(packet)

	@classmethod
	def decode(cls, data, packet, command_code):
		"""
		Do not call this method directly -- use ClockSAL.decode
		"""
		
		argument = ord(data[0])
		data = data[1:]
		
		if argument != 0x03:
			warnings.warn('Request refresh argument != 3 (got %d instead)' % argument, UserWarning)
			return None, data

		return cls(packet), data
	
	def encode(self):
		return super(ClockRequestSAL, self).encode() + [
			0x11, 0x03
		]


class ClockApplication(object):
	"""
	This class is called in the cbus.protocol.applications.APPLICATIONS dict in
	order to describe how to decode clock and timekeeping application events
	recieved from the network.
	
	Do not call this class directly.
	"""
	@classmethod
	def decode_sal(cls, data, packet):
		"""
		Decodes a clock and timekeeping application packet and returns it's
		SAL(s).
		"""
		return ClockSAL.decode(data, packet)

