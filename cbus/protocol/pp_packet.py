#!/usr/bin/env python
# cbus/protocol/pp_packet.py - Point to Multipoint packet decoder
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
from six import byte2int, indexbytes
from six.moves import range
from typing import Optional, List

from cbus.common import (
    DestinationAddressType, PriorityClass, CAL, BRIDGE_LENGTHS,
    add_cbus_checksum)
from cbus.protocol.base_packet import BasePacket
from cbus.protocol.cal import REQUESTS, AnyCAL
from cbus.protocol.cal.reply import ReplyCAL


class PointToPointPacket(BasePacket):

    def __init__(
            self, checksum: bool = True,
            priority_class: PriorityClass = PriorityClass.CLASS_4,
            unit_address: int = 0, bridge_address: int = 0,
            hops: Optional[List[int]] = None,
            cals: Optional[List[AnyCAL]] = None):
        super(PointToPointPacket, self).__init__(
            checksum=checksum,
            destination_address_type=DestinationAddressType.POINT_TO_POINT,
            priority_class=priority_class)

        if hops is None:
            self.hops = []
            self.pm_bridged = False
            if bridge_address != 0:
                raise ValueError('bridge_address was specified but are no '
                                 'hops to traverse!')
        else:
            self.hops = hops
            self.pm_bridged = True
            if bridge_address <= 0:
                raise ValueError('hops were specified, but there is no '
                                 'bridge_address!')

        self.unit_address = unit_address
        self.cals = cals or []

    @classmethod
    def decode_packet(cls, data: bytes, checksum: bool,
                      priority_class: PriorityClass) -> PointToPointPacket:

        # now decode the unit address or bridge address
        params = {}
        if indexbytes(data, 1) == 0x00:
            # this is a unit address
            unit_address = byte2int(data)
            data = data[2:]
        else:
            params['bridge_address'] = byte2int(data)

            bridge_length = BRIDGE_LENGTHS[indexbytes(data, 1)]

            data = data[2:]
            params['hops'] = hops = []

            for x in range(bridge_length):
                # get all the hops
                hops.append(byte2int(data[0]))
                data = data[1:]

            unit_address = byte2int(data)

            data = data[1:]


        # now decode messages
        cals = []
        while data:
            # find the cal
            cmd = byte2int(data)
            if cmd & 0xE0 == CAL.REPLY:  # flick off the lower bits
                # REPLY
                reply_len = (cmd & 0x1F)

                data = data[1:]
                reply_data = data[:reply_len]
                data = data[reply_len:]

                cal = ReplyCAL.decode_cal(reply_data)
            elif cmd & 0xE0 == CAL.STANDARD_STATUS:
                # STATUS (standard)
                raise NotImplementedError('standard status cal')
            elif cmd & 0xE0 == CAL.EXTENDED_STATUS:
                # status (extended)
                raise NotImplementedError('extended status cal')
            else:
                handler = REQUESTS[cmd]
                data, cal = handler.decode_cal(data)

            cals.append(cal)

        return PointToPointPacket(
            checksum=checksum, priority_class=priority_class,
            unit_address=unit_address, cals=cals, **params)

    def encode(self, source_addr=None) -> bytes:

        if self.pm_bridged:
            raise NotImplementedError('bridged ptp packets')
        else:
            o = bytearray([
                self.unit_address,
                0,  # no bridge
            ])

        # new encode the cals
        for cal in self.cals:
            o += cal.encode()

        # join the packet
        p = bytes(bytearray(super(PointToPointPacket, self)._encode() + o))

        # checksum it, if needed.
        if self.checksum:
            p = add_cbus_checksum(p)

        return b16encode(p)

    def __repr__(self):  # pragma: no cover
        return '<%s object: unit_address=%r, pm_bridged=%r, cal=%r>' % (
            self.__class__.__name__, self.unit_address, self.pm_bridged,
            self.cal)
