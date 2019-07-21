#!/usr/bin/env python
# utils.py - Helpers for unit tests
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

from typing import Optional
import unittest

from cbus.protocol.base_packet import BasePacket
from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.pp_packet import PointToPointPacket
from cbus.protocol.packet import decode_packet


class CBusTestCase(unittest.TestCase):

    def decode_packet(
            self, data: bytes,
            checksum: bool = True,
            strict: bool = True,
            server_packet: bool = True,
            expected_position: Optional[int] = None) -> Optional[BasePacket]:
        """
        Decodes a packet, and validates that the buffer position has consumed
        the packet.

        See ``cbus.packet.decode_packet`` for details.

        :param expected_position: If None (default), expect to consume the
                                  entire input data. Otherwise, an integer
                                  number of bytes that were expected to be
                                  consumed.
        :return: The parsed packet, or None if no packet was parsed.
        """
        if expected_position is None:
            expected_position = len(data)

        packet, position = decode_packet(data, checksum, strict, server_packet)
        self.assertEqual(
            expected_position, position,
            'Expected to parse the whole input data: {}'.format(data))

        return packet

    def decode_pm(
            self, data: bytes,
            checksum: bool = True,
            strict: bool = True,
            server_packet: bool = True,
            expected_position: Optional[int] = None)\
            -> PointToMultipointPacket:
        """Decodes and asserts a packet is PointToMultipointPacket."""

        p = self.decode_packet(
            data, checksum, strict, server_packet, expected_position)
        self.assertIsInstance(p, PointToMultipointPacket)
        return p

    def decode_pp(
            self, data: bytes,
            checksum: bool = True,
            strict: bool = True,
            server_packet: bool = True,
            expected_position: Optional[int] = None) \
            -> PointToPointPacket:
        """Decodes and asserts a packet is PointToPointPacket."""

        p = self.decode_packet(
            data, checksum, strict, server_packet, expected_position)
        self.assertIsInstance(p, PointToPointPacket)
        return p
