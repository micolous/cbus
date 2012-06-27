#!/usr/bin/env python
# cbus/protocol/pp_packet.py - Point to Multipoint packet decoder
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
from cbus.common import *

class PointToPointPacket(BasePacket):
	
	@classmethod
	def decode_packet(cls, data, checksum, flags, destination_address_type, rc, dp, priority_class):
		
		packet = cls(checksum, flags, destination_address_type, rc, dp, priority_class)
		
		# now decode the unit address or bridge address
		
		if data[1] == '\x00':
			# this is a unit address
			packet.pm_bridged = False
			packet.unit_address = ord(data[0])
			data = data[2:]
			
		else:
			# this is a bridge address
			packet.pm_bridged = True
			packet.bridge_address = ord(data[0])
			
			bridge_length = BRIDGE_LENGTHS[ord(data[1])]
			
			data = data[2:]
			packet.hops = []
			
			for x in range(bridge_length):
				# get all the hops
				packet.hops.append(data[0])
				data = data[1:]
			
			packet.unit_address = ord(data[0])
		
		# now read CAL data
		
		
