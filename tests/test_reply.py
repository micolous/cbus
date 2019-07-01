#!/usr/bin/env python
# test_reply.py - Reply CAL unit test
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
from cbus.protocol.cal.reply import ReplyCAL


class ClipsalReplyTest(unittest.TestCase):
    def test_s9_2(self):
        """Example in s9.2 (Serial Interface Guide) of decoding a reply CAL"""
        p, r = decode_packet(b'8604990082300328', server_packet=True)
        self.assertIsInstance(p, PointToPointPacket)
        self.assertEqual(p.source_address, 4)
        self.assertEqual(p.unit_address, 0x99)
        self.assertEqual(len(p.cal), 1)

        self.assertIsInstance(p.cal[0], ReplyCAL)
        self.assertEqual(p.cal[0].parameter, 0x30)
        self.assertEqual(p.cal[0].data, b'\x03')

        self.assertEqual(p.encode(), b'8604990082300328')


if __name__ == '__main__':
    unittest.main()
