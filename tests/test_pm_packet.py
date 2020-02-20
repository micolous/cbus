#!/usr/bin/env python
# test_pm_packet.py - Point to Multipoint packet tests
# Copyright 2012-2020 Michael Farrell <micolous+git@gmail.com>
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

from cbus.common import Application
from cbus.protocol.application.lighting import LightingOffSAL
from cbus.protocol.application.status_request import StatusRequestSAL
from cbus.protocol.pm_packet import PointToMultipointPacket

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


class InternalPointToMultipointTest(CBusTestCase):

    def test_invalid_multiple_application_sal(self):
        """Argument validation - SALs from different applications."""
        with self.assertRaisesRegex(
                ValueError, r'SAL .+ of application ff, .+ has application 38'):
            PointToMultipointPacket(sals=[
                LightingOffSAL(1),
                StatusRequestSAL(level_request=True, group_address=1,
                                 child_application=Application.LIGHTING),
            ])

    def test_remove_sals(self):
        # create a packet
        p = PointToMultipointPacket(sals=LightingOffSAL(1))
        self.assertEqual(1, len(p))

        p.clear_sal()
        self.assertEqual(0, len(p))

        # We should be able to add a different app
        p.append_sal(StatusRequestSAL(level_request=True, group_address=1,
                                      child_application=Application.LIGHTING))
        self.assertEqual(1, len(p))

        # Adding another lighting SAL should fail
        with self.assertRaisesRegex(ValueError, r'has application ff$'):
            p.append_sal(LightingOffSAL(1))
        self.assertEqual(1, len(p))

    def test_invalid_sal(self):
        p = PointToMultipointPacket()
        with self.assertRaisesRegex(ValueError, 'application .+ None'):
            p.encode_packet()

        p.application = 0x100
        with self.assertRaisesRegex(ValueError, 'application .+ in range'):
            p.encode_packet()


if __name__ == '__main__':
    unittest.main()
