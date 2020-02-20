#!/usr/bin/env python
# test_cal.py - CAL tests
# Copyright 2019 Michael Farrell <micolous+git@gmail.com>
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

from cbus.common import Application, GroupState
from cbus.protocol.cal.extended import ExtendedCAL
from cbus.protocol.cal.report import (
    BinaryStatusReport, LevelStatusReport, manchester_decode,
    manchester_encode)

from .utils import CBusTestCase


class ClipsalExtendedStatusTest(CBusTestCase):
    def _check_s9_1_result(self, p, expected_start, expected_len):
        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], ExtendedCAL)
        self.assertFalse(p[0].externally_initated)
        self.assertEqual(p[0].child_application, Application.LIGHTING)
        self.assertEqual(p[0].block_start, expected_start)

        # Check the status of the report
        self.assertIsInstance(p[0].report, BinaryStatusReport)
        self.assertEqual(len(p[0].report), expected_len)
        for i, r in enumerate(p[0].report):
            i += p[0].block_start
            # GA 1 - 8 are "off", others missing
            expected = GroupState.OFF if 1 <= i <= 8 else GroupState.MISSING
            self.assertEqual(r, expected, f'#{i} in group {p}')

    def test_s9_1_exstat(self):
        """Examples in serial interface user guide s9.1"""
        # Status reply, SMART mode, EXSTAT on
        p = self.decode_pp(
            b'86999900F8003800A8AA0200000000000000000000000000000000000000C4'
            b'\r\n')

        self._check_s9_1_result(p, 0, 88)

        p = self.decode_pp(
            b'86999900F800385800000000000000000000000000000000000000000000C0'
            b'\r\n')

        self._check_s9_1_result(p, 88, 88)

        # Note: documentation has wrong checksum (8F != 6A)
        p = self.decode_pp(
            b'86999900F60038B000000000000000000000000000000000000000006A'
            b'\r\n')

        self._check_s9_1_result(p, 176, 80)

    def test_p49_manchester_coding(self):
        self.assertEqual(manchester_decode(b'\xaa\xaa'), 0x00)
        self.assertEqual(manchester_decode(b'\x00\x00'), None)
        self.assertEqual(manchester_decode(b'\x95\x99'), 0x57)
        self.assertEqual(manchester_decode(b'\x55\x55'), 0xff)

        self.assertEqual(manchester_encode(0x00), b'\xaa\xaa')
        self.assertEqual(manchester_encode(None), b'\x00\x00')
        self.assertEqual(manchester_encode(0x57), b'\x95\x99')
        self.assertEqual(manchester_encode(0xff), b'\x55\x55')


class InternalStatusTest(CBusTestCase):

    def _check_level_response(self, p, expected_start, expected_len):
        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], ExtendedCAL)
        self.assertFalse(p[0].externally_initated)
        self.assertEqual(p[0].child_application, Application.LIGHTING)
        self.assertEqual(p[0].block_start, expected_start)

        # Check the status of the report
        self.assertIsInstance(p[0].report, LevelStatusReport)
        self.assertEqual(len(p[0].report), expected_len)
        for i, r in enumerate(p[0].report):
            i += p[0].block_start
            # GA 1 - 8 are "off", others missing
            expected = 0 if 1 <= i <= 8 else None
            self.assertEqual(r, expected, f'#{i} in group {p}')

    def test_level_response(self):
        p = self.decode_pp(
            b'86FFFF00F90738000000AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA00000000A4'
            b'\r\n')
        self._check_level_response(p, 0, 11)

        p = self.decode_pp(
            b'86FFFF00F907380B0000000000000000000000000000000000000000000039'
            b'\r\n')
        self._check_level_response(p, 11, 11)

        p = self.decode_pp(
            b'86FFFF00F7073816000000000000000000000000000000000000000030\r\n')
        self._check_level_response(p, 22, 10)

    def test_manchester_api(self):
        b = bytearray(4)
        b2 = manchester_encode(0xff, b)
        self.assertEqual(b, b'\x55\x55\0\0')
        self.assertIs(b, b2)

        # don't overwrite the old data
        manchester_encode(0x00, b, 2)
        self.assertEqual(b, b'\x55\x55\xaa\xaa')

        # None = no changes
        manchester_encode(None, b, 1)
        self.assertEqual(b, b'\x55\x55\xaa\xaa')

        # Out of bounds
        with self.assertRaises(IndexError):
            manchester_encode(0x42, b, 10)
        self.assertEqual(b, b'\x55\x55\xaa\xaa')


if __name__ == '__main__':
    unittest.main()
