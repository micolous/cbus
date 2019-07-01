#!/usr/bin/env python
# test_lighting.py - Lighting Application unit tests
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

import unittest

from cbus.protocol.packet import decode_packet
from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.application.lighting import (
    LightingOffSAL, LightingOnSAL, LightingRampSAL, LightingTerminateRampSAL)
from cbus.common import APP_LIGHTING


class ClipsalLightingTest(unittest.TestCase):
    def test_s6_4(self):
        """Examples in serial interface guide, s6.4"""
        # Switch on light at GA 8
        p, r = decode_packet('\\0538000108BAg', server_packet=False)

        self.assertIsInstance(p, PointToMultipointPacket)
        self.assertEqual(len(p.sal), 1)

        self.assertIsInstance(p.sal[0], LightingOffSAL)
        self.assertEqual(p.sal[0].group_address, 8)

        # check that it encodes properly again
        self.assertEqual(p.encode(), '0538000108BA')
        self.assertEqual(p.confirmation, 'g')

        # concatenated packet
        p, r = decode_packet('\\05380001087909090A25h', server_packet=False)

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

    def test_s2_11(self):
        """Examples in Lighting Application s2.11"""
        # switch on light at GA 0x93
        p, r = decode_packet('\\0538007993B7j', server_packet=False)

        self.assertIsInstance(p, PointToMultipointPacket)
        self.assertEqual(len(p.sal), 1)

        self.assertIsInstance(p.sal[0], LightingOnSAL)
        self.assertEqual(p.sal[0].group_address, 0x93)

        # check that it encodes properly again
        self.assertEqual(p.encode(), '0538007993B7')
        self.assertEqual(p.confirmation, 'j')

    def test_s9_1(self):
        """Examples in quick start guide, s9.1"""
        # turn on light 0x21
        p, r = decode_packet('\\053800792129i', server_packet=False)

        self.assertIsInstance(p, PointToMultipointPacket)
        self.assertEqual(len(p.sal), 1)

        self.assertIsInstance(p.sal[0], LightingOnSAL)
        self.assertEqual(p.sal[0].group_address, 0x21)

        # check that it encodes properly again
        self.assertEqual(p.encode(), '053800792129')
        self.assertEqual(p.confirmation, 'i')

        # turn off light 0x21
        p, r = decode_packet('\\0538000121A1k', server_packet=False)

        self.assertIsInstance(p, PointToMultipointPacket)
        self.assertEqual(len(p.sal), 1)

        self.assertIsInstance(p.sal[0], LightingOffSAL)
        self.assertEqual(p.sal[0].group_address, 0x21)

        # check that it encodes properly again
        self.assertEqual(p.encode(), '0538000121A1')
        self.assertEqual(p.confirmation, 'k')

        # ramp light 0x21 to 50% over 4 seconds
        p, r = decode_packet('\\0538000A217F19l', server_packet=False)

        self.assertIsInstance(p, PointToMultipointPacket)
        self.assertEqual(len(p.sal), 1)

        self.assertIsInstance(p.sal[0], LightingRampSAL)
        self.assertEqual(p.sal[0].group_address, 0x21)
        self.assertEqual(p.sal[0].duration, 4)
        # rounding must be done to 2 decimal places, as the value isn't
        # actually 50%, but 49.8039%.  next value is 50.1%.
        self.assertEqual(round(p.sal[0].level, 2), 0.5)

        # check that it encodes properly again
        self.assertEqual(p.encode(), '0538000A217F19')
        self.assertEqual(p.confirmation, 'l')


class InternalLightingTest(unittest.TestCase):
    def test_lighting_encode_decode(self):
        "self-made tests of encode then decode"

        orig = PointToMultipointPacket(application=APP_LIGHTING)
        orig.source_address = 5
        orig.sal.append(LightingOnSAL(orig, 27))

        data = orig.encode()

        d, r = decode_packet(data)
        self.assertIsInstance(orig, PointToMultipointPacket)
        self.assertEqual(orig.source_address, d.source_address)
        self.assertEqual(len(orig.sal), len(d.sal))

        self.assertIsInstance(d.sal[0], LightingOnSAL)
        self.assertEqual(orig.sal[0].group_address, d.sal[0].group_address)

        # ensure there is no remaining data to be parsed
        self.assertIsNone(r)

    def test_lighting_encode_decode_client(self):
        "self-made tests of encode then decode, with packets from a client."

        orig = PointToMultipointPacket(application=APP_LIGHTING)
        orig.sal.append(LightingOnSAL(orig, 27))

        data = orig.encode()

        d, r = decode_packet(data, server_packet=False)
        self.assertIsInstance(orig, PointToMultipointPacket)
        self.assertEqual(len(orig.sal), len(d.sal))

        self.assertIsInstance(d.sal[0], LightingOnSAL)
        self.assertEqual(orig.sal[0].group_address, d.sal[0].group_address)

        # ensure there is no remaining data to be parsed
        self.assertIsNone(r)


class LightingRegressionTest(unittest.TestCase):
    def test_issue2(self):
        """Handle the null lighting packet described in Issue #2."""
        # Lighting packet from the server, lighting application, source address
        # 0x06. Sometimes cbus units emit these null lighting commands because
        # of an off-by-one issue?
        p, r = decode_packet('05063800BD')

        self.assertIsInstance(p, PointToMultipointPacket)
        self.assertEqual(p.application, 0x38)
        self.assertEqual(p.source_address, 0x06)
        self.assertEqual(len(p.sal), 0)

        self.assertIsNone(r)


if __name__ == '__main__':
    unittest.main()
