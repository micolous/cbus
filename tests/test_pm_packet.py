#!/usr/bin/env python
# test_pm_packet.py - Point to Multipoint packet tests
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
from cbus.protocol.application.lighting import LightingOffSAL


class ClipsalPointToMultipointTest(unittest.TestCase):
    def test_s4_2_9_2(self):
        """Serial interface guide s4.2.9.2 (page 23) test"""
        # first test
        p, m = decode_packet('\\0538000108BAg', server_packet=False)

        self.assertIsInstance(p, PointToMultipointPacket)
        self.assertFalse(p.status_request)
        self.assertEqual(p.application, 0x38)
        self.assertEqual(len(p.sal), 1)

        self.assertIsInstance(p.sal[0], LightingOffSAL)
        self.assertEqual(p.sal[0].group_address, 8)

        self.assertEqual(p.confirmation, 'g')

        self.assertIsNone(m)

        # second test
        p, m = decode_packet('\\05FF007A38004Ah', server_packet=False)

        self.assertIsInstance(p, PointToMultipointPacket)
        self.assertTrue(p.status_request)
        self.assertEqual(p.application, 0x38)
        self.assertEqual(p.group_address, 0)
        self.assertEqual(p.confirmation, 'h')

        # no remainder
        self.assertIsNone(m)


if __name__ == '__main__':
    unittest.main()
