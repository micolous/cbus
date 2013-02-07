#!/usr/bin/env python
# cbus/protocol/cal/reply.py - CAL REPLY packet
# Copyright 2013 Michael Farrell <micolous+git@gmail.com>
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
import warnings

__all__ = [
	'ReplyCAL',
]



class ReplyCAL(object):
	"""
	Reply cal
	
	Not a way at the moment to tell between responses to RECALL, GETSTATUS and IDENTIFY?
	"""
	
	def __init__(self, packet, parameter, data):
		self.packet = packet
		self.parameter = parameter
		self.data = data
	
	@classmethod
	def decode_cal(cls, data, packet):
		"""
		Decodes reply CAL.
		"""
		
		cal = ReplyCAL(packet, ord(data[0]), data[1:])
		
		return cal
	
	def encode(self):
		assert (0 <= self.parameter <= 255), 'parameter must be in range 0..255'
		assert (len(self.data) < 0x1F), 'must be less than 31 bytes of data'
		return [
			(CAL_RES_REPLY | (len(self.data) + 1)),
			self.parameter
		] + [ord(c) for c in self.data]
		
	def __repr__(self):
		return '<%s object: parameter=%r, data=%r>' % (
			self.__class__.__name__,
			self.parameter,
			self.data
		)




