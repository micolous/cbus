#!/usr/bin/env python
# cbus/protocol/dm_packet.py - Device Management Packet decoder
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
from cbus.protocol.base_packet import BasePacket
from cbus.protocol.application import APPLICATIONS
from cbus.common import *
from base64 import b16encode

class PointToMultipointPacket(BasePacket):
	status_request = False
	sal = []
	
	@classmethod
	def decode_packet(cls, data, checksum, flags, destination_address_type, rc, dp, priority_class):
		packet = cls(checksum, flags, destination_address_type, rc, dp, priority_class)
		
			
		return packet
		
	def encode(self, source_addr=None):
		raise NotImplemented, "status request not implemented"

		# encode the remainder
		o = [
			self.application,
			0,
		]
		for x in self.sal:
				o += x.encode()
		
		# join the packet
		p = (''.join((chr(x) for x in (
			super(PointToMultipointPacket, self)._encode() + o
		))))
		
		# checksum it, if needed.
		if self.checksum:
			p = add_cbus_checksum(p)
		
		return b16encode(p)
		
