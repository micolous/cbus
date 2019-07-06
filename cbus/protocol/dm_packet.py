#!/usr/bin/env python
# cbus/protocol/dm_packet.py - Device Management Packet decoder
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
from __future__ import annotations

from base64 import b16encode

from cbus.protocol.base_packet import BasePacket
from cbus.common import (
    PriorityClass, DestinationAddressType, add_cbus_checksum)


class DeviceManagementPacket(BasePacket):
    def __init__(
            self, checksum: bool = True,
            priority_class: PriorityClass = PriorityClass.CLASS_2,
            parameter: int = 0,
            value: int = 0):
        super().__init__(
            checksum=checksum,
            destination_address_type=
            DestinationAddressType.POINT_TO_POINT_TO_MULTIPOINT,
            dp=True,
            priority_class=priority_class,
        )

        self.parameter = parameter
        self.value = value

    @staticmethod
    def decode_packet(data: bytes, checksum: bool,
                      priority_class: PriorityClass) -> DeviceManagementPacket:
        # serial interface guide s10.2
        # A3 pp 00 vv
        # where:
        #  pp = parameter number
        #  vv = value

        parameter = data[0]
        if data[1] != 0:
            raise ValueError('second byte of DeviceManagementPacket must be 0')

        value = data[2]

        if len(data) != 3:
            raise ValueError(
                'Unexpected DeviceManagementPacket payload length')

        return DeviceManagementPacket(
            checksum=checksum, priority_class=priority_class,
            parameter=parameter, value=value)

    def encode(self) -> bytes:
        # encode the remainder
        parameter = self.parameter & 0xff
        value = self.value & 0xff

        p = super().encode() + bytes([parameter, 0, value])

        # checksum it, if needed.
        if self.checksum:
            p = add_cbus_checksum(p)

        return b16encode(p)
