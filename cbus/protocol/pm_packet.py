#!/usr/bin/env python
# cbus/protocol/pm_packet.py - Point to Multipoint packet decoder
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

class PointToMultipointPacket(BasePacket):
	status_request = False
	
	@classmethod
	def decode_packet(cls, data, checksum, flags, destination_address_type, rc, dp, priority_class):
		packet = cls(checksum, flags, destination_address_type, rc, dp, priority_class)
		# serial interface guide s4.2.9.2
		
		# is this referencing an application
		packet.application = ord(data[0])
		assert ord(data[1]) == 0x00, "Routing data in PM message?"
		
		if packet.application == 0xFF:
			# status request
			packet.status_request = True
			
			# ...decode it.
			data = data[2:]
			
			raise NotImplemented, "status request not implemented"
		else:
			# SAL data (application request)
			packet.status_request = False
			
			# find an application handler
			handler = APPLICATIONS[packet.application]
			
			data = data[2:]
			packet.sal = handler.decode_sal(data, packet)
			
		return packet
		
		
		
