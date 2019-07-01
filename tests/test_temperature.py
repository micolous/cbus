#!/usr/bin/env python
# test_temperature.py - Temperature broadcast unit tests
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
from cbus.protocol.application.temperature import TemperatureBroadcastSAL
from cbus.common import APP_TEMPERATURE


class ClipsalTemperatureTest(unittest.TestCase):
    def test_s9_11(self):
        """Example in temperature broadcast application guide, s9.11"""
        # Temperature of 25 degrees at group 5
        # note, the guide actually states that there is a checksum, but no
        # checksum is actually on the packet!
        p, r = decode_packet(b'\\05190002056477g', server_packet=False)

        self.assertIsInstance(p, PointToMultipointPacket)
        self.assertEqual(len(p.sal), 1)

        self.assertIsInstance(p.sal[0], TemperatureBroadcastSAL)
        self.assertEqual(p.sal[0].group_address, 5)
        self.assertEqual(p.sal[0].temperature, 25)

        # check that it encodes properly again
        self.assertEqual(p.encode(), b'05190002056477')
        self.assertEqual(p.confirmation, b'g')


class InternalTemperatureTest(unittest.TestCase):
    def test_temperature_encode_decode(self):
        """self-made tests of encode then decode"""

        orig = PointToMultipointPacket(application=APP_TEMPERATURE)
        orig.source_address = 5
        orig.sal.append(TemperatureBroadcastSAL(orig, 10, 0.5))
        orig.sal.append(TemperatureBroadcastSAL(orig, 11, 56))

        data = orig.encode()

        d, r = decode_packet(data)
        self.assertIsInstance(orig, PointToMultipointPacket)
        self.assertEqual(orig.source_address, d.source_address)
        self.assertEqual(len(orig.sal), len(d.sal))

        for x in range(len(d.sal)):
            self.assertIsInstance(d.sal[x], TemperatureBroadcastSAL)
            self.assertEqual(orig.sal[x].group_address, d.sal[x].group_address)
            self.assertEqual(orig.sal[x].temperature, d.sal[x].temperature)

        # ensure there is no remaining data to be parsed
        self.assertIsNone(r)


if __name__ == '__main__':
    unittest.main()
