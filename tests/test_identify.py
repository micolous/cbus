#!/usr/bin/env python
# test_identify.py - Identify CAL unit test
# Copyright 2013-2019 Michael Farrell <micolous+git@gmail.com>
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
from cbus.protocol.pp_packet import PointToPointPacket
from cbus.protocol.cal.identify import IdentifyCAL


class BennettIdentifyTest(unittest.TestCase):
    def test_get_unit_type(self):
        """
        Example of 'get unit type' (identify type) from Geoffry Bennett's
        protocol reverse engineering docs

        """
        p, r = decode_packet(
            b'\\0699002101', server_packet=False, checksum=False)

        self.assertIsInstance(p, PointToPointPacket)

        self.assertEqual(p.unit_address, 0x99)
        self.assertEqual(len(p.cal), 1)

        self.assertIsInstance(p.cal[0], IdentifyCAL)
        self.assertEqual(p.cal[0].attribute, 1)

        self.assertEqual(p.encode(), b'0699002101')


if __name__ == '__main__':
    unittest.main()
