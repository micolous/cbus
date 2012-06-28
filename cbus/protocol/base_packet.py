#!/usr/bin/env python
# cbus/protocol/base_packet.py - Skeleton class for basic packets
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


class BasePacket(object):
	confirmation = None
	def __init__(self, checksum=True, flags=None, destination_address_type=None, rc=None, dp=None, priority_class=None):
		# base packet implementation.
		self.checksum = checksum
		
		#self.flags = flags
		self.destination_address_type = destination_address_type
		self.rc = rc
		self.dp = dp
		self.priority_class = priority_class

	def _encode(self):
		# do checks to make sure the maths will work out.
		assert self.destination_address_type == self.destination_address_type & 0x07, 'destination_address_type > 0x07'
		assert self.rc == self.rc & 0x03, 'rc > 0x03'
		assert self.priority_class == self.priority_class & 0x03, 'priority_class > 0x03'
		
		flags = \
			self.destination_address_type + \
			(self.rc << 3) + \
			(0x20 if self.dp else 0x00) + \
			(self.priority_class << 6)
		
		#print self.destination_address_type, self.rc << 3, 0x20 if self.dp else 0x00, self.priority_class << 6
		assert 0 <= flags <= 0xFF, 'flags not between 0 and 255 (%r)!' % flags
		
		return [flags]


class SpecialClientPacket(BasePacket):
	"""
	Client -> PCI communications have some special packets, which we make subclasses of SpecialClientPacket to make them entirely seperate from normal packets.
	
	These have non-standard methods for serialisation.
	"""
	checksum = False
	destination_address_type = None
	rc = None
	dp = None
	priority_class = None
	
	def __init__(self):
		pass
	
	def _encode(self):
		return ''

