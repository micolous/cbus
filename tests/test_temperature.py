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

from .utils import CBusTestCase


class ClipsalTemperatureTest(CBusTestCase):
    def test_s9_11(self):
        """Example in temperature broadcast application guide, s9.11"""
        # Temperature of 25 degrees at group 5
        # Note: The guide states that there is a checksum on the packet,
        # but there is actually no checksum.
        p = self.decode_pm(
            b'\\051900020564g\r', server_packet=False, checksum=False)

        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], TemperatureBroadcastSAL)
        self.assertEqual(p[0].group_address, 5)
        self.assertEqual(p[0].temperature, 25)

        # check that it encodes properly again
        p.checksum = True
        self.assertEqual(p.encode_packet(), b'05190002056477')
        self.assertEqual(p.confirmation, b'g')


class InternalTemperatureTest(CBusTestCase):
    def test_temperature_encode_decode(self):
        """self-made tests of encode then decode"""

        orig = PointToMultipointPacket(
            sals=[TemperatureBroadcastSAL(10, 0.5),
                  TemperatureBroadcastSAL(11, 56)]
        )
        orig.source_address = 5
        data = orig.encode_packet() + b'\r\n'

        d = self.decode_pm(data)
        self.assertIsInstance(orig, PointToMultipointPacket)
        self.assertEqual(orig.source_address, d.source_address)
        self.assertEqual(len(orig), len(d))

        for x in range(len(d)):
            self.assertIsInstance(d[x], TemperatureBroadcastSAL)
            self.assertEqual(orig[x].group_address, d[x].group_address)
            self.assertEqual(orig[x].temperature, d[x].temperature)


if __name__ == '__main__':
    unittest.main()
