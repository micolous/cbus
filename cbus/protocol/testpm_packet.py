#!/usr/bin/env python
# cbus/protocol/testpm_packet.py - Point to Multipoint packet tests
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


import unittest
from cbus.protocol.packet import decode_packet
from cbus.protocol.pm_packet import PointToMultipointPacket

class PMSerialInterfaceGuideTests(unittest.TestCase):
	def runTest(self):
		p = decode_packet('\\05FF007A38004Ag', server_packet=False)
		
		self.assertIsInstance(p, PointToMultipointPacket)
		self.assertEqual(p.status_request, True)
		self.assertEqual(p.application, 0x38)
		self.assertEqual(p.group_address, 0)

