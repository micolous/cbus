#!/usr/bin/env python3
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

import abc
from base64 import b16encode
from dataclasses import dataclass
from typing import Optional

from cbus.common import DestinationAddressType, PriorityClass

__all__ = [
    'BasePacket',
    'InvalidPacket',
    'SpecialClientPacket',
    'SpecialServerPacket',
]


class BasePacket(abc.ABC):
    def __init__(
            self,
            checksum: bool = True,
            destination_address_type:
            DestinationAddressType = DestinationAddressType.UNSET,
            rc: int = 0,
            dp: bool = False,
            priority_class: PriorityClass = PriorityClass.CLASS_4):
        # base packet implementation.
        self.checksum = checksum

        self.destination_address_type = destination_address_type
        self.rc = rc
        self.dp = dp
        self.priority_class = priority_class
        self.confirmation = None
        self.source_address = None

    @property
    def flags(self) -> int:
        return ((self.destination_address_type & 0x07) |
                ((self.rc & 0x02) << 3) |
                (0x20 if self.dp else 0) |
                ((self.priority_class & 0x03) << 6))

    @abc.abstractmethod
    def encode(self) -> bytes:
        if self.source_address is None:
            return bytes([self.flags])
        else:
            source_address = self.source_address & 0xff
            return bytes([self.flags, source_address])

    def encode_packet(self) -> bytes:
        return b16encode(self.encode())


class _SpecialPacket(BasePacket, abc.ABC):
    def __init__(self):
        super(_SpecialPacket, self).__init__(
            checksum=False)

    @abc.abstractmethod
    def encode(self) -> bytes:
        raise NotImplementedError('encode')

    def encode_packet(self):
        return self.encode()


class SpecialClientPacket(_SpecialPacket, abc.ABC):
    """
    Client -> PCI communications have some special packets, which we make
    subclasses of SpecialClientPacket to make them entirely separate from
    normal packets.

    These have non-standard methods for serialisation.
    """

    def __repr__(self):
        return f'{self.__class__.__name__}()'


class SpecialServerPacket(_SpecialPacket, abc.ABC):
    """
    PCI -> Client has some special packets that we make subclasses of this,
    because they're different to regular packets.

    These have non-standard serialisation methods.
    """
    pass


@dataclass(init=True)
class InvalidPacket(_SpecialPacket):
    """Invalid packet data."""
    payload: bytes
    exception: Optional[Exception] = None

    def encode(self):
        return self.payload
