#!/usr/bin/env python
# cbus/protocol/application/testclock.py - Clock and Timekeeping Application Unit Tests
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
from cbus.protocol.application.clock import *
from cbus.common import *
from datetime import time, date

class S23_13_1_Test(unittest.TestCase):
	def runTest(self):
		"Example in s23.13.1 of decoding a time"
		# Set network time to 10:43:23 with no DST offset
		# Slight change from guide:
		p, r = decode_packet('\\05DF000D010A2B1700C2g', server_packet=False)
		
		self.assertIsInstance(p, PointToMultipointPacket)
		self.assertEqual(len(p.sal), 1)
		
		self.assertIsInstance(p.sal[0], ClockUpdateSAL)
		self.assertTrue(p.sal[0].is_time)
		self.assertFalse(p.sal[0].is_date)
		self.assertIsInstance(p.sal[0].val, time)
		
		self.assertEqual(p.sal[0].val.hour, 10)
		self.assertEqual(p.sal[0].val.minute, 43)
		self.assertEqual(p.sal[0].val.second, 23)
		# Library doesn't handle DST offset, so this flag is dropped.
		
		## check that it encodes properly again
		# fuzzy match to allow packet that has no DST information
		self.assertIn(p.encode(), ['05DF000D010A2B1700C2', '05DF000D010A2B17FFC3'])
		self.assertEqual(p.confirmation, 'g')
		
		
class S23_13_2_Test(unittest.TestCase):
	def runTest(self):
		"Example in s23.13.2 of decoding a date"
		# Set network date to 2005-02-25 (Friday)
		p, r = decode_packet('\\05DF000E0207D502190411g', server_packet=False)
		self.assertIsInstance(p, PointToMultipointPacket)
		self.assertEqual(len(p.sal), 1)
		
		self.assertIsInstance(p.sal[0], ClockUpdateSAL)
		self.assertTrue(p.sal[0].is_date)
		self.assertFalse(p.sal[0].is_time)
		self.assertIsInstance(p.sal[0].val, date)
		
		self.assertEqual(p.sal[0].val.year, 2005)
		self.assertEqual(p.sal[0].val.month, 2)
		self.assertEqual(p.sal[0].val.day, 25)
		self.assertEqual(p.sal[0].val.weekday(), 4) # friday

		## check that it encodes properly again
		self.assertIn(p.encode(), '05DF000E0207D502190411')
		self.assertEqual(p.confirmation, 'g')

		
class S23_13_3_Test(unittest.TestCase):
	def runTest(self):
		"Example in s23.13.3 of decoding request refresh"
		# Request refreeh command
		# documentation is wrong here:
		#  - says      05DF00100C
		#  - should be 05DF00110308
		
		p, r = decode_packet('\\05DF00110308g', server_packet=False)
		self.assertIsInstance(p, PointToMultipointPacket)
		self.assertEqual(len(p.sal), 1)
		
		self.assertIsInstance(p.sal[0], ClockRequestSAL)
		
		## check that it encodes properly again
		self.assertIn(p.encode(), '05DF00110308')
		self.assertEqual(p.confirmation, 'g')

