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

from base64 import b16encode
from six import byte2int, indexbytes
from six.moves import range

from cbus.common import CLASS_4, DAT_PP, BRIDGE_LENGTHS, add_cbus_checksum
from cbus.protocol.base_packet import BasePacket
from cbus.protocol.cal import REQUESTS
from cbus.protocol.cal.reply import ReplyCAL


class PointToPointPacket(BasePacket):

    def __init__(self,
                 checksum=True,
                 priority_class=CLASS_4,
                 unit_address=0,
                 bridge_address=0,
                 hops=None):
        super(PointToPointPacket, self).__init__(
            checksum, DAT_PP, 0, False, priority_class)

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

        self.cal = []

    @classmethod
    def decode_packet(cls, data, checksum, flags, destination_address_type, rc,
                      dp, priority_class):

        packet = cls(checksum, priority_class)

        # now decode the unit address or bridge address

        if indexbytes(data, 1) == 0x00:
            # this is a unit address
            packet.pm_bridged = False
            packet.unit_address = byte2int(data)
            data = data[2:]

        else:
            # this is a bridge address
            packet.pm_bridged = True
            packet.bridge_address = byte2int(data)

            bridge_length = BRIDGE_LENGTHS[indexbytes(data, 1)]

            data = data[2:]
            packet.hops = []

            for x in range(bridge_length):
                # get all the hops
                packet.hops.append(byte2int(data[0]))
                data = data[1:]

            packet.unit_address = byte2int(data)

            data = data[1:]

        # now decode messages
        # packet.cal = []
        while data:
            # find the cal
            cmd = byte2int(data)
            if cmd & 0xE0 == 0x80:  # flick off the lower bits
                # REPLY
                reply_len = (cmd & 0x1F)

                data = data[1:]
                reply_data = data[:reply_len]
                data = data[reply_len:]

                cal = ReplyCAL.decode_cal(reply_data, packet)

                # print cal
                # print packet
                # print ord(data)
            elif cmd & 0xE0 == 0xC0:
                # STATUS (standard)
                raise NotImplementedError('standard status cal')
            elif cmd & 0xE0 == 0xE0:
                # status (extended)
                raise NotImplementedError('extended status cal')
            else:
                handler = REQUESTS[cmd]
                data, cal = handler.decode_cal(data, packet)

            packet.cal.append(cal)

        # now read CAL data
        # print "%s" % data

        return packet

    def encode(self, source_addr=None):

        if self.pm_bridged:
            raise NotImplementedError('bridged ptp packets')
        else:
            o = [
                self.unit_address,
                0,  # no bridge
            ]

        # new encode the cals
        for cal in self.cal:
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
