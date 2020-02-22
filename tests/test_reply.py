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

from cbus.protocol.cal.reply import ReplyCAL

from .utils import CBusTestCase


class ClipsalReplyTest(CBusTestCase):
    def test_s9_2(self):
        """Example in s9.2 (Serial Interface Guide) of decoding a reply CAL"""
        p = self.decode_pp(b'8604990082300328\r\n', from_pci=True)
        self.assertEqual(p.source_address, 4)
        self.assertEqual(p.unit_address, 0x99)
        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], ReplyCAL)
        self.assertEqual(p[0].parameter, 0x30)
        self.assertEqual(p[0].data, b'\x03')

        self.assertEqual(p.encode_packet(), b'8604990082300328')


if __name__ == '__main__':
    unittest.main()
