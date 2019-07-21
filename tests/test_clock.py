#!/usr/bin/env python
# test_clock.py - Clock and Timekeeping Application Unit Tests
#
# Copyright 2012-2019 Michael Farrell <micolous+git@gmail.com>
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

from __future__ import absolute_import

from datetime import time, date
import unittest

from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.application.clock import ClockRequestSAL, ClockUpdateSAL

from .utils import CBusTestCase


class ClipsalClockTest(CBusTestCase):
    def test_s23_13_1(self):
        """Example in s23.13.1 of decoding a time."""
        # Set network time to 10:43:23 with no DST offset
        # Slight change from guide:
        p = self.decode_pm(
            b'\\05DF000D010A2B1700C2g\r', server_packet=False)
        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], ClockUpdateSAL)
        self.assertTrue(p[0].is_time)
        self.assertFalse(p[0].is_date)
        self.assertIsInstance(p[0].val, time)

        self.assertEqual(p[0].val.hour, 10)
        self.assertEqual(p[0].val.minute, 43)
        self.assertEqual(p[0].val.second, 23)

        # Library doesn't handle DST offset, so this flag is dropped.

        # check that it encodes properly again
        # fuzzy match to allow packet that has no DST information
        self.assertIn(p.encode(),
                      [b'05DF000D010A2B1700C2', b'05DF000D010A2B17FFC3'])
        self.assertEqual(p.confirmation, b'g')

    def test_s23_13_2(self):
        """Example in s23.13.2 of decoding a date."""
        # Set network date to 2005-02-25 (Friday)
        p = self.decode_pm(
            b'\\05DF000E0207D502190411g\r', server_packet=False)
        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], ClockUpdateSAL)
        self.assertTrue(p[0].is_date)
        self.assertFalse(p[0].is_time)
        self.assertIsInstance(p[0].val, date)

        self.assertEqual(p[0].val.year, 2005)
        self.assertEqual(p[0].val.month, 2)
        self.assertEqual(p[0].val.day, 25)
        self.assertEqual(p[0].val.weekday(), 4)  # friday

        # check that it encodes properly again
        self.assertEqual(p.encode(), b'05DF000E0207D502190411')
        self.assertEqual(p.confirmation, b'g')

    def test_s23_13_3(self):
        """Example in s23.13.3 of decoding request refresh."""
        # Request refresh command
        # documentation is wrong here:
        #  - says      05DF00100C
        #  - should be 05DF00110308

        p = self.decode_pm(
            b'\\05DF00110308g\r', server_packet=False)
        self.assertIsInstance(p, PointToMultipointPacket)
        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], ClockRequestSAL)

        # check that it encodes properly again
        self.assertEqual(p.encode(), b'05DF00110308')
        self.assertEqual(p.confirmation, b'g')


if __name__ == '__main__':
    unittest.main()
