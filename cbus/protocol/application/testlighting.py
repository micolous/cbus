#!/usr/bin/env python
# cbus/protocol/application/testlighting.py - Lighting Application unit tests
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
from cbus.common import *

class LightingSerialInterfaceGuideTests(unittest.TestCase):
	def runTest(self):
		"Examples in serial interface guide, s6.4"
		# Switch on light at GA 8
		p = decode_packet('\\0538000108BAg', server_packet=False)
		
		self.assertIsInstance(p, PointToMultipointPacket)
		self.assertEqual(len(p.sal), 1)
		
		self.assertIsInstance(p.sal[0], LightingOffSAL)
		self.assertEqual(p.sal[0].group_address, 8)
		
		# check that it encodes properly again
		self.assertEqual(p.encode(), '0538000108BA')
		self.assertEqual(p.confirmation, 'g')
		
		
		p = decode_packet('\\05380001087909090A25h', server_packet=False)
		
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
		
		# check that it encodes properly again
		self.assertEqual(p.encode(), '05380001087909090A25')
		self.assertEqual(p.confirmation, 'h')
		

class LightingApplicationTests(unittest.TestCase):
	def runTest(self):
		"Examples in Lighting Application s2.11"
		# switch on light at GA 0x93
		p = decode_packet('\\0538007993B7j', server_packet=False)
		
		self.assertIsInstance(p, PointToMultipointPacket)
		self.assertEqual(len(p.sal), 1)
		
		self.assertIsInstance(p.sal[0], LightingOnSAL)
		self.assertEqual(p.sal[0].group_address, 0x93)
		
		# check that it encodes properly again
		self.assertEqual(p.encode(), '0538007993B7')
		self.assertEqual(p.confirmation, 'j')


class LightingQuickStartGuideTests(unittest.TestCase):
	def runTest(self):
		"Examples in quick start guide, s9.1"
		# turn on light 0x21
		p = decode_packet('\\053800792129i', server_packet=False)
		
		self.assertIsInstance(p, PointToMultipointPacket)
		self.assertEqual(len(p.sal), 1)
		
		self.assertIsInstance(p.sal[0], LightingOnSAL)
		self.assertEqual(p.sal[0].group_address, 0x21)

		# check that it encodes properly again
		self.assertEqual(p.encode(), '053800792129')
		self.assertEqual(p.confirmation, 'i')
		
		# turn off light 0x21
		p = decode_packet('\\0538000121A1k', server_packet=False)
		
		self.assertIsInstance(p, PointToMultipointPacket)
		self.assertEqual(len(p.sal), 1)
		
		self.assertIsInstance(p.sal[0], LightingOffSAL)
		self.assertEqual(p.sal[0].group_address, 0x21)

		# check that it encodes properly again
		self.assertEqual(p.encode(), '0538000121A1')
		self.assertEqual(p.confirmation, 'k')
		
		# ramp light 0x21 to 50% over 4 seconds
		p = decode_packet('\\0538000A217F19l', server_packet=False)
		
		self.assertIsInstance(p, PointToMultipointPacket)
		self.assertEqual(len(p.sal), 1)
		
		self.assertIsInstance(p.sal[0], LightingRampSAL)
		self.assertEqual(p.sal[0].group_address, 0x21)
		self.assertEqual(p.sal[0].duration, 4)
		# rounding must be done to 2 decimal places, as the value isn't actually
		# 50%, but 49.8039%.  next value is 50.1%.
		self.assertEqual(round(p.sal[0].level, 2), 0.5)
		
		# check that it encodes properly again
		self.assertEqual(p.encode(), '0538000A217F19')		
		self.assertEqual(p.confirmation, 'l')


class EncodeDecodeTests(unittest.TestCase):
	def runTest(self):
		"self-made tests of encode then decode"
		
		orig = PointToMultipointPacket(application=APP_LIGHTING)
		orig.source_address = 5
		orig.sal.append(LightingOnSAL(orig, 27))
		
		data = orig.encode()

		d = decode_packet(data)
		self.assertIsInstance(orig, PointToMultipointPacket)		
		self.assertEqual(orig.source_address, d.source_address)
		self.assertEqual(len(orig.sal), len(d.sal))
		
		self.assertIsInstance(d.sal[0], LightingOnSAL)
		self.assertEqual(orig.sal[0].group_address, orig.sal[0].group_address)


