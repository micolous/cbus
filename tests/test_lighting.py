#!/usr/bin/env python
# test_lighting.py - Lighting Application unit tests
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

import unittest

from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.application.lighting import (
    LightingOffSAL, LightingOnSAL, LightingRampSAL, LightingTerminateRampSAL)
from .utils import CBusTestCase


class ClipsalSerialLightingTest(CBusTestCase):
    """Examples in Serial Interface Guide"""

    def test_s6_4(self):
        """Examples in s6.4"""
        # Switch on light at GA 8
        p = self.decode_pm(b'\\0538000108BAg\r', from_pci=False)

        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], LightingOffSAL)
        self.assertEqual(p[0].group_address, 8)

        # check that it encodes properly again
        self.assertEqual(p.encode_packet(), b'0538000108BA')
        self.assertEqual(p.confirmation, b'g')

        # concatenated packet
        p = self.decode_pm(
            b'\\05380001087909090A25h\r', from_pci=False)

        self.assertEqual(len(p), 3)

        # turn off light 8
        self.assertIsInstance(p[0], LightingOffSAL)
        self.assertEqual(p[0].group_address, 8)

        # turn on light 9
        self.assertIsInstance(p[1], LightingOnSAL)
        self.assertEqual(p[1].group_address, 9)

        # terminate ramp on light 10)
        self.assertIsInstance(p[2], LightingTerminateRampSAL)
        self.assertEqual(p[2].group_address, 10)

        # check that it encodes properly again
        self.assertEqual(p.encode_packet(), b'05380001087909090A25')
        self.assertEqual(p.confirmation, b'h')


class ClipsalLightingTest(CBusTestCase):
    """Examples in Clipsal Lighting Application doc"""

    def test_s2_11(self):
        """Examples in s2.11"""
        # switch on light at GA 0x93
        p = self.decode_pm(b'\\0538007993B7j\r', from_pci=False)
        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], LightingOnSAL)
        self.assertEqual(p[0].group_address, 0x93)

        # check that it encodes properly again
        self.assertEqual(p.encode_packet(), b'0538007993B7')
        self.assertEqual(p.confirmation, b'j')


class ClipsalQuickLightingTest(CBusTestCase):
    """Examples in Quick Start Guide"""

    def test_s9_1(self):
        """Examples in s9.1"""
        # turn on light 0x21
        p = self.decode_pm(b'\\053800792129i\r', from_pci=False)
        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], LightingOnSAL)
        self.assertEqual(p[0].group_address, 0x21)

        # check that it encodes properly again
        self.assertEqual(p.encode_packet(), b'053800792129')
        self.assertEqual(p.confirmation, b'i')

        # turn off light 0x21
        p = self.decode_pm(b'\\0538000121A1k\r', from_pci=False)
        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], LightingOffSAL)
        self.assertEqual(p[0].group_address, 0x21)

        # check that it encodes properly again
        self.assertEqual(p.encode_packet(), b'0538000121A1')
        self.assertEqual(p.confirmation, b'k')

        # ramp light 0x21 to 50% over 4 seconds
        p = self.decode_pm(b'\\0538000A217F19l\r', from_pci=False)
        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], LightingRampSAL)
        self.assertEqual(p[0].group_address, 0x21)
        self.assertEqual(p[0].duration, 4)
        self.assertEqual(p[0].level, 127)

        # check that it encodes properly again
        self.assertEqual(p.encode_packet(), b'0538000A217F19')
        self.assertEqual(p.confirmation, b'l')


class InternalLightingTest(CBusTestCase):
    def test_lighting_encode_decode(self):
        """test of encode then decode"""

        orig = PointToMultipointPacket(sals=LightingOnSAL(27))
        orig.source_address = 5

        data = orig.encode_packet() + b'\r\n'

        d = self.decode_pm(data)
        self.assertEqual(orig.source_address, d.source_address)
        self.assertEqual(len(orig), len(d))

        self.assertIsInstance(d[0], LightingOnSAL)
        self.assertEqual(orig[0].group_address, d[0].group_address)

    def test_lighting_encode_decode_client(self):
        """test of encode then decode, with packets from a client"""

        orig = PointToMultipointPacket(sals=LightingOnSAL(27))

        data = b'\\' + orig.encode_packet() + b'\r'

        d = self.decode_pm(data, from_pci=False)
        self.assertEqual(len(orig), len(d))

        self.assertIsInstance(d[0], LightingOnSAL)
        self.assertEqual(orig[0].group_address, d[0].group_address)

    def test_invalid_ga(self):
        """test argument validation"""
        with self.assertRaises(ValueError):
            PointToMultipointPacket(sals=LightingOnSAL(999))
        with self.assertRaises(ValueError):
            PointToMultipointPacket(sals=LightingOffSAL(-1))

    def test_slow_ramp(self):
        """test very slow ramps"""
        p1 = PointToMultipointPacket(
            sals=LightingRampSAL(1, 18*60, 255)).encode_packet()
        p2 = PointToMultipointPacket(
            sals=LightingRampSAL(1, 17*60, 255)).encode_packet()
        self.assertEqual(p1, p2)


class LightingRegressionTest(CBusTestCase):
    def test_issue2(self):
        """Handle the null lighting packet described in Issue #2."""
        # Lighting packet from the server, lighting application, source address
        # 0x06. Sometimes cbus units emit these null lighting commands because
        # of an off-by-one issue?
        p = self.decode_pm(b'05063800BD\r\n')

        self.assertEqual(p.application, 0x38)
        self.assertEqual(p.source_address, 0x06)
        self.assertEqual(len(p), 0)


if __name__ == '__main__':
    unittest.main()
