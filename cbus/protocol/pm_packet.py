#!/usr/bin/env python3
# cbus/protocol/pm_packet.py - Point to Multipoint packet decoder
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

from typing import Iterator, Optional, Sequence, Union

from cbus.common import (
    Application, PriorityClass, DestinationAddressType, add_cbus_checksum)
from cbus.protocol.application import get_application
from cbus.protocol.application.sal import SAL
from cbus.protocol.base_packet import BasePacket


class PointToMultipointPacket(BasePacket, Sequence[SAL]):
    """
    Point to Multipoint Packet

    Ref: Serial Interface User Guide, s4.2.9.2
    """

    def __init__(
            self, checksum: bool = True,
            priority_class: PriorityClass = PriorityClass.CLASS_4,
            application: Optional[Application] = None,
            sals: Optional[Union[SAL, Sequence[SAL]]] = None):
        super(PointToMultipointPacket, self).__init__(
            checksum=checksum,
            destination_address_type=DestinationAddressType
            .POINT_TO_MULTIPOINT,
            priority_class=priority_class)
        self.application = application
        self._sals = []

        if isinstance(sals, SAL):
            self.append_sal(sals)
        else:
            for sal in sals:
                self.append_sal(sal)

    def __repr__(self):  # pragma: no cover
        return (
                '<{} object: application={}, source_address={}, '
                'sals={}>'.format(
                    self.__class__.__name__, self.application,
                    self.source_address,
                    self._sals))

    def append_sal(self, sal: SAL) -> None:
        sal_application = int(sal.application)
        if self.application is None:
            self.application = sal_application
        elif self.application != sal_application:
            raise ValueError(
                f'SAL {sal:r} is part of application {sal_application:x}, '
                f'but this Packet has application {self.application:x}')

        self._sals.append(sal)

    def clear_sal(self) -> None:
        """Removes all SALs from this packet."""
        self._sals = []
        self.application = None

    def __len__(self) -> int:
        """Returns the number of SALs associated with this packet."""
        return len(self._sals)

    def __getitem__(self, item: int) -> SAL:
        """Returns the indexed SAL associated with this packet."""
        return self._sals[item]

    def __iter__(self) -> Iterator[SAL]:
        """Returns an iterator over the SALs associated with this packet."""
        return iter(self._sals)

    def index(self, x: SAL, start: int = ..., end: int = ...) -> int:
        """
        Finds a SAL within this packet.

        :raises ValueError: if not present
        """
        return self._sals.index(x, start, end)

    @classmethod
    def decode_packet(
            cls, data: bytes, checksum: bool, priority_class: PriorityClass)\
            -> PointToMultipointPacket:
        application = Application(data[0])
        if data[1] != 0x00:
            raise ValueError('Routing data in PM message?')

        # find an application handler
        handler = get_application(application)
        data = data[2:]
        sals = handler.decode_sals(data)

        return cls(
            checksum=checksum, priority_class=priority_class,
            application=application, sals=sals)

    def encode(self):
        if self.application is None:
            raise ValueError('application must not be None')

        a = int(self.application)
        if a < 0 or a > 0xff:
            raise ValueError('application must be in range 0..255 '
                             '(got {})'.format(a))

        o = bytearray([a, 0])
        for x in self._sals:
            o += x.encode()

        # join the packet
        p = super().encode() + bytes(o)

        # checksum it, if needed.
        if self.checksum:
            p = add_cbus_checksum(p)

        return p
