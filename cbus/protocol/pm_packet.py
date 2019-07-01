#!/usr/bin/env python
# cbus/protocol/pm_packet.py - Point to Multipoint packet decoder
# Copyright 2012 Michael Farrell <micolous+git@gmail.com>
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
from cbus.protocol.base_packet import BasePacket
from cbus.protocol.application import APPLICATIONS
from cbus.common import *
from base64 import b16encode


class PointToMultipointPacket(BasePacket):
    status_request = False
    level_request = False
    group_address = None
    application = None

    def __init__(self,
                 checksum=True,
                 priority_class=CLASS_4,
                 application=None,
                 status_request=False):
        super(PointToMultipointPacket, self).__init__(checksum, None, DAT_PM, 0,
                                                      False, priority_class)
        self.application = application
        self.status_request = status_request
        self.sal = []

    def __repr__(self):  # pragma: no cover
        return '<%s object: application=%r, source_address=%r, status_req=%r, %s>' % (
            self.__class__.__name__, self.application, self.source_address,
            self.status_request,
            ('level_reqest=%r' %
             (self.level_request,)) if self.status_request else
            ('sal=%r' % (self.sal,)))

    @classmethod
    def decode_packet(cls, data, checksum, flags, destination_address_type, rc,
                      dp, priority_class):
        packet = cls(checksum, priority_class)
        # serial interface guide s4.2.9.2

        # is this referencing an application
        packet.application = ord(data[0])
        assert ord(data[1]) == 0x00, "Routing data in PM message?"

        if packet.application == 0xFF:
            # status request
            packet.status_request = True

            # ...decode it.
            data = data[2:]

            if data[0] in ('\x7A', '\xFA'):
                # 7A version of the status request (binary)
                # FA is deprecated and "shouldn't be used".  ha ha.
                data = data[1:]
                packet.level_request = False
            elif data[:2] == '\x73\x07':
                # 7307 version of the status request (levels, in v4)
                data = data[2:]
                packet.level_request = True
            else:
                raise NotImplemented, 'unknown status request type %r' % data[0]

            # now read the application
            packet.application = ord(data[0])
            packet.group_address = ord(data[1])

            assert packet.group_address % 0x20 == 0, 'group_address report must be a multiple of 0x20'

            return packet
        else:
            # SAL data (application request)
            packet.status_request = False

            # find an application handler
            handler = APPLICATIONS[packet.application]

            data = data[2:]
            packet.sal = handler.decode_sal(data, packet)

        return packet

    def encode(self, source_addr=None):
        # TODO: Implement source address

        if self.status_request:
            # this a level request
            a = int(self.application)
            ga = int(self.group_address)

            assert 0 <= a <= 0xFF, 'application must be in range 0..255 (got %r)' % a
            assert 0 <= ga <= 0xFF, 'groupaddress must be in range 0..255 (got %r)' % ga

            l = [0x73, 0x07] if self.level_request else [0x7A]
            o = [0xFF] + l + [packet.application, packet.group_address]

        else:
            assert self.application != None, 'application must not be None'
            a = int(self.application)
            assert 0 <= a <= 0xFF, 'application must be in range 0..255 (got %r)' % a
            # encode the remainder
            o = [
                a,
                0,
            ]
            for x in self.sal:
                o += x.encode()

        # join the packet
        p = (''.join(
            (chr(x)
             for x in (super(PointToMultipointPacket, self)._encode() + o))))

        # checksum it, if needed.
        if self.checksum:
            p = add_cbus_checksum(p)

        return b16encode(p)
