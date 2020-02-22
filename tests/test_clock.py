#!/usr/bin/env python
# test_clock.py - Clock and Timekeeping Application Unit Tests
#
# Copyright 2012-2020 Michael Farrell <micolous+git@gmail.com>
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

from datetime import time, date, timedelta, datetime
import unittest

from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.application.clock import (
    ClockRequestSAL, ClockUpdateSAL, clock_update_sal)

from .utils import CBusTestCase


class ClipsalClockTest(CBusTestCase):
    def test_s23_13_1(self):
        """Example in s23.13.1 of decoding a time."""
        # Set network time to 10:43:23 with no DST offset
        expected_time = time(10, 43, 23)
        # Slight change from guide:
        p = self.decode_pm(
            b'\\05DF000D010A2B1700C2g\r', from_pci=False)
        self.assertEqual(len(p), 1)

        s = p[0]
        self.assertIsInstance(s, ClockUpdateSAL)
        self.assertTrue(s.is_time)
        self.assertFalse(s.is_date)
        self.assertEqual(s.val, expected_time)

        # Library doesn't handle DST offset, so this flag is dropped.

        # check that it encodes properly again
        # fuzzy match to allow packet that has no DST information
        self.assertIn(p.encode_packet(),
                      [b'05DF000D010A2B1700C2', b'05DF000D010A2B17FFC3'])
        self.assertEqual(p.confirmation, b'g')

        # check that the same value would encode
        p = PointToMultipointPacket(sals=clock_update_sal(expected_time))
        self.assertIn(p.encode_packet(),
                      [b'05DF000D010A2B1700C2', b'05DF000D010A2B17FFC3'])

    def test_s23_13_2(self):
        """Example in s23.13.2 of decoding a date."""
        # Set network date to 2005-02-25 (Friday)
        expected_date = date(2005, 2, 25)
        p = self.decode_pm(
            b'\\05DF000E0207D502190411g\r', from_pci=False)
        self.assertEqual(len(p), 1)

        s = p[0]
        self.assertIsInstance(s, ClockUpdateSAL)
        self.assertTrue(s.is_date)
        self.assertFalse(s.is_time)
        self.assertEqual(s.val, expected_date)

        # check that it encodes properly again
        self.assertEqual(p.encode_packet(), b'05DF000E0207D502190411')
        self.assertEqual(p.confirmation, b'g')

        # check that the same value would encode
        p = PointToMultipointPacket(sals=clock_update_sal(expected_date))
        self.assertEqual(p.encode_packet(), b'05DF000E0207D502190411')

    def test_s23_13_3(self):
        """Example in s23.13.3 of decoding request refresh."""
        # Request refresh command
        # documentation is wrong here:
        #  - says      05DF00100C
        #  - should be 05DF00110308

        p = self.decode_pm(
            b'\\05DF00110308g\r', from_pci=False)
        self.assertIsInstance(p, PointToMultipointPacket)
        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], ClockRequestSAL)

        # check that it encodes properly again
        self.assertEqual(p.encode_packet(), b'05DF00110308')
        self.assertEqual(p.confirmation, b'g')


class InternalClockTest(CBusTestCase):

    def test_unknown_object(self):
        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            clock_update_sal(timedelta(1))

        sal = ClockUpdateSAL(time(0,0,0))
        sal.val = timedelta(1)
        with self.assertRaises(TypeError):
            sal.encode()

    def test_datetime_object(self):
        moment = datetime(2019, 12, 31, 23, 59, 13)
        p = PointToMultipointPacket(sals=clock_update_sal(moment))

        p = self.decode_pm(b'\\' + p.encode_packet() + b'g\r', from_pci=False)
        d = t = None
        self.assertEqual(2, len(p))
        for sal in p:
            self.assertIsInstance(sal, ClockUpdateSAL)
            if sal.is_time and not sal.is_date:
                self.assertIsNone(t)
                t = sal.val
            elif sal.is_date and not sal.is_time:
                self.assertIsNone(d)
                d = sal.val

        self.assertEqual(moment.date(), d)
        self.assertEqual(moment.time(), t)

    def test_invalid_clock_request(self):
        # Bad variable (01 != 03)
        with self.assertWarnsRegex(UserWarning, r'refresh argument != 3'):
            p = self.decode_pm(b'\\05DF0011010Ag\r', from_pci=False)

        self.assertEqual(0, len(p))

        # Bad variable but with a valid variable after it
        with self.assertWarnsRegex(UserWarning, r'refresh argument != 3'):
            p = self.decode_pm(b'\\05DF0011011103F6g\r', from_pci=False)

        self.assertEqual(1, len(p))
        self.assertIsInstance(p[0], ClockRequestSAL)


if __name__ == '__main__':
    unittest.main()
