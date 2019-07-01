#!/usr/bin/env python
# cbus/protocol/base_packet.py - Skeleton class for basic packets
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

__all__ = [
    'BasePacket', 'SpecialPacket', 'SpecialClientPacket', 'SpecialServerPacket'
]


class BasePacket(object):
    confirmation = None
    source_address = None

    def __init__(self,
                 checksum=True,
                 destination_address_type=None,
                 rc=None,
                 dp=None,
                 priority_class=None):
        # base packet implementation.
        self.checksum = checksum

        self.destination_address_type = destination_address_type
        self.rc = rc
        self.dp = dp
        self.priority_class = priority_class

    def _encode(self):
        # do checks to make sure the maths will work out.
        if self.destination_address_type > 0x07:
            raise ValueError('destination_address_type > 0x07')
        if self.rc > 0x03:
            raise ValueError('rc > 0x03')
        if self.priority_class > 0x03:
            raise ValueError('priority_class > 0x03')

        flags = (self.destination_address_type + (self.rc << 3) +
                 (0x20 if self.dp else 0x00) + (self.priority_class << 6))

        # print(self.destination_address_type, self.rc << 3,
        #       0x20 if self.dp else 0x00, self.priority_class << 6)
        if flags < 0 or flags > 0xff:
            raise ValueError('flags not in range 0..255 ({})'.format(flags))

        if self.source_address:
            source_address = int(self.source_address)
            if source_address < 0 or source_address > 0xff:
                raise ValueError('source_address set, but not in range 0..255 '
                                 '({})'.format(source_address))

            return [flags, source_address]
        else:
            return [flags]


class SpecialPacket(BasePacket):
    """

    """
    checksum = False
    destination_address_type = None
    rc = None
    dp = None
    priority_class = None

    def __init__(self):
        pass

    def _encode(self):
        return ''


class SpecialClientPacket(SpecialPacket):
    """
    Client -> PCI communications have some special packets, which we make
    subclasses of SpecialClientPacket to make them entirely separate from
    normal packets.

    These have non-standard methods for serialisation.
    """

    pass


class SpecialServerPacket(SpecialPacket):
    """
    PCI -> Client has some special packets that we make subclasses of this,
    because they're different to regular packets.

    These have non-standard serialisation methods.
    """

    pass
