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

from six import byte2int, indexbytes
from six.moves import range
from typing import Iterator, Optional, Sequence, Tuple

from cbus.common import (
    DestinationAddressType, PriorityClass, CAL, BRIDGE_LENGTHS,
    add_cbus_checksum)
from cbus.protocol.base_packet import BasePacket
from cbus.protocol.cal import REQUESTS, AnyCAL
from cbus.protocol.cal.extended import ExtendedCAL
from cbus.protocol.cal.reply import ReplyCAL


class PointToPointPacket(BasePacket, Sequence[AnyCAL]):

    def __init__(
            self, checksum: bool = True,
            priority_class: PriorityClass = PriorityClass.CLASS_4,
            unit_address: int = 0, bridge_address: int = 0,
            hops: Optional[Sequence[int]] = None,
            cals: Optional[Sequence[AnyCAL]] = None):
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
            self.hops = list(hops)
            self.pm_bridged = True
            if bridge_address <= 0:
                raise ValueError('hops were specified, but there is no '
                                 'bridge_address!')

        self.unit_address = unit_address
        self._cals = list(cals) or []

    def __len__(self) -> int:
        """Returns the number of CALs associated with this packet."""
        return len(self._cals)

    def __getitem__(self, item: int) -> AnyCAL:
        """Returns the indexed CAL associated with this packet."""
        return self._cals[item]

    def __iter__(self) -> Iterator[AnyCAL]:
        """Returns an iterator over the CALs associated with this packet."""
        return iter(self._cals)

    def index(self, x: AnyCAL, start: int = ..., end: int = ...) -> int:
        """
        Finds a CAL within this packet.

        :raises ValueError: if not present
        """
        return self._cals.index(x, start, end)

    @classmethod
    def decode_cal(cls, data: bytes) -> Tuple[AnyCAL, int]:
        # find the cal
        cmd = byte2int(data)
        if cmd & 0xE0 == CAL.REPLY:  # flick off the lower bits
            # REPLY
            cal_end = (cmd & 0x1F) + 1
            if len(data) < cal_end:
                raise ValueError(f'Invalid reply CAL, need {cal_end} bytes '
                                 f'but got {len(data)}')
            reply_data = data[1:cal_end]
            return ReplyCAL.decode_cal(reply_data), cal_end
        elif cmd & 0xE0 == CAL.STANDARD_STATUS:
            # STATUS (standard)
            # Note: these packets never contain addressing information,
            # so we probably can't support them without a full state
            # machine anyway.
            raise NotImplementedError('standard status cal')
        elif cmd & 0xE0 == CAL.EXTENDED_STATUS:
            # EXSTAT / Extended status
            # Note: s9.1 examples have incorrect status length, shows 24 but
            # is actually 25. Actual hardware tests show correct length.
            cal_end = (cmd & 0x1f) + 1
            if len(data) < cal_end:
                raise ValueError(f'Invalid reply CAL, need {cal_end} bytes '
                                 f'but got {len(data)}')

            reply_data = data[1:cal_end]
            return ExtendedCAL.decode_cal(reply_data), cal_end
        else:
            handler = REQUESTS[cmd]
            return handler.decode_cal(data)

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
                hops.append(byte2int(data))
                data = data[1:]

            unit_address = byte2int(data)

            data = data[1:]

        # now decode messages
        cals = []
        while data:
            cal, cal_len = cls.decode_cal(data)
            data = data[cal_len:]
            cals.append(cal)

        return PointToPointPacket(
            checksum=checksum, priority_class=priority_class,
            unit_address=unit_address, cals=cals, **params)

    def encode(self) -> bytes:
        if self.pm_bridged:
            raise NotImplementedError('bridged ptp packets')
        else:
            o = bytearray([
                self.unit_address,
                0,  # no bridge
            ])

        # new encode the cals
        for cal in self._cals:
            o += cal.encode()

        # join the packet
        p = super().encode() + bytes(o)

        # checksum it, if needed.
        if self.checksum:
            p = add_cbus_checksum(p)

        return p

    def __repr__(self):  # pragma: no cover
        return '<%s object: unit_address=%r, pm_bridged=%r, cals=%r>' % (
            self.__class__.__name__, self.unit_address, self.pm_bridged,
            self._cals)
