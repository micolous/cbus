#!/usr/bin/env python
# test_special_packet.py - Unit tests for special packets
# Copyright 2020 Michael Farrell <micolous+git@gmail.com>
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

from typing import Optional
import unittest

from cbus.protocol.error_packet import PCIErrorPacket
from cbus.protocol.po_packet import PowerOnPacket
from cbus.protocol.reset_packet import ResetPacket
from cbus.protocol.scs_packet import SmartConnectShortcutPacket
from .utils import CBusTestCase


class SpecialPCICommandTest(CBusTestCase):

    def check_packet_type(self, data: bytes,
                          typ=None,
                          checksum: bool = True,
                          strict: bool = True,
                          from_pci: bool = True,
                          expected_position: Optional[int] = None):
        p = self.decode_packet(
            data, checksum, strict, from_pci, expected_position)

        if typ is None:
            self.assertIsNone(p)
        else:
            self.assertIsInstance(p, typ)

        return p

    # Packets from PCI
    def test_power_on(self):
        self.check_packet_type(b'++', PowerOnPacket, expected_position=1)

    def test_error(self):
        self.check_packet_type(b'!', PCIErrorPacket, expected_position=1)

    # Packets to PCI
    def test_reset_packet(self):
        self.check_packet_type(b'~~~', ResetPacket, from_pci=False,
                               expected_position=1)

    def test_toolkit_stupid(self):
        self.check_packet_type(b'null\r', None, from_pci=False,
                               expected_position=4)

    def test_smart_connect(self):
        self.check_packet_type(b'|\r', SmartConnectShortcutPacket,
                               from_pci=False, expected_position=2)
        self.check_packet_type(b'||\r', SmartConnectShortcutPacket,
                               from_pci=False, expected_position=2)

    def test_discard(self):
        self.check_packet_type(b'hello?\\053800792129i\r', None, from_pci=False,
                               expected_position=6)


if __name__ == '__main__':
    unittest.main()
