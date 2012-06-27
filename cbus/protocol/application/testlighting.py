#!/usr/bin/env python
# cbus/protocol/application/lighting_test.py - Lighting Application unit tests
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
from cbus.protocol.application.lighting import *

class LightingTests(unittest.TestCase):
	def runTest(self):
		# Examples in serial interface guide, s6.4
		p = decode_packet('\\0538000108BA')
		
		self.assertIsInstance(p, PointToMultipointPacket)
		self.assertEqual(len(p.sal), 1)
		
		self.assertIsInstance(p.sal[0], LightingOffSAL)
		self.assertEqual(p.sal[0].group_address, 8)
		
		
		p = decode_packet('\\05380001087909090A25')
		
		self.assertIsInstance(p, PointToMultipointPacket)
		self.assertEqual(len(p.sal), 3)
		
		# turn off light 8
		self.assertIsInstance(p.sal[0], LightingOffSAL)
		self.assertEqual(p.sal[0].group_address, 8)
		
		# turn on light 9		
		self.assertIsInstance(p.sal[1], LightingOnSAL)
		self.assertEqual(p.sal[1].group_address, 9)
		
		# terminate ramp on light 10)
		self.assertIsInstance(p.sal[2], LightingTerminateRampSAL)
		self.assertEqual(p.sal[2].group_address, 10)

