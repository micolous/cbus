#!/usr/bin/env python
# cbus/protocol/cal/reply.py - CAL REPLY packet
# Copyright 2013-2019 Michael Farrell <micolous+git@gmail.com>
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

from dataclasses import dataclass

from cbus.common import CAL

__all__ = [
    'ReplyCAL',
]


@dataclass
class ReplyCAL:
    """
    Reply CAL (Device and Network Management Command).

    Ref: Serial Interface Guide, s7.1

    There is no way to tell between ``RECALL``, ``GETSTATUS`` and ``IDENTIFY``
    responses at the protocol level, without keeping state. This class treats
    all ``REPLY`` messages in the same way.

    ``parameter`` is the attribute requested for ``IDENTIFY`` responses.
    """

    parameter: int
    data: bytes

    @classmethod
    def decode_cal(cls, data: bytes) -> ReplyCAL:
        """
        Decodes reply CAL.
        """

        return ReplyCAL(parameter=data[0], data=data[1:])

    def encode(self) -> bytes:
        parameter = self.parameter & 0xff
        data = self.data[:0x1e]
        return bytes([CAL.REPLY | (len(data) + 1), parameter]) + data
