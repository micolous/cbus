#!/usr/bin/env python
# test_enable.py - Enable control unit tests
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
from cbus.protocol.application.enable import EnableSetNetworkVariableSAL


class ClipsalEnableTest(unittest.TestCase):
    def test_s8_11(self):
        """Example in enable control application guide, s8.11 (page 7)"""
        # Set the network variable 0x37 to 0x82
        p, r = decode_packet(b'\\05CB0002378275g', server_packet=False)

        self.assertIsInstance(p, PointToMultipointPacket)
        self.assertEqual(len(p.sal), 1)

        self.assertIsInstance(p.sal[0], EnableSetNetworkVariableSAL)
        self.assertEqual(p.sal[0].variable, 0x37)
        self.assertEqual(p.sal[0].value, 0x82)

        # check that it encodes properly again
        self.assertEqual(p.encode(), b'05CB0002378275')
        self.assertEqual(p.confirmation, b'g')


if __name__ == '__main__':
    unittest.main()
