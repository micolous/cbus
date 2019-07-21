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

from cbus.protocol.application.lighting import LightingOffSAL
from cbus.protocol.application.status_request import StatusRequestSAL

from .utils import CBusTestCase


class ClipsalPointToMultipointTest(CBusTestCase):
    def test_s4_2_9_2_1(self):
        """Serial interface guide s4.2.9.2 (page 23) first test."""
        p = self.decode_pm(b'\\0538000108BAg\r', server_packet=False)

        self.assertEqual(p.application, 0x38)
        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], LightingOffSAL)
        self.assertEqual(p[0].group_address, 8)

        self.assertEqual(p.confirmation, b'g')

    def test_s4_2_9_2_2(self):
        """Serial interface guide s4.2.9.2 (page 23) second test."""
        p = self.decode_pm(b'\\05FF007A38004Ah\r', server_packet=False)

        self.assertEqual(len(p), 1)

        self.assertIsInstance(p[0], StatusRequestSAL)

        self.assertEqual(p[0].child_application, 0x38)
        self.assertEqual(p[0].group_address, 0)
        self.assertEqual(p.confirmation, b'h')



if __name__ == '__main__':
    unittest.main()
