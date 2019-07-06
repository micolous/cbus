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

from cbus.common import CAL

__all__ = [
    'ReplyCAL',
]


class ReplyCAL(object):
    """
    Reply CAL (Device and Network Management Command).

    Ref: Serial Interface Guide, s7.1

    There is no way to tell between ``RECALL``, ``GETSTATUS`` and ``IDENTIFY``
    responses at the protocol level, without keeping state. This class treats
    all ``REPLY`` messages in the same way.

    ``parameter`` is the attribute requested for ``IDENTIFY`` responses.
    """

    def __init__(self, parameter: int, data: bytes):
        self.parameter = parameter
        self.data = data

    @classmethod
    def decode_cal(cls, data):
        """
        Decodes reply CAL.
        """

        cal = ReplyCAL(data[0], data[1:])

        return cal

    def encode(self) -> bytes:
        parameter = self.parameter & 0xff
        data = self.data[:0x1e]
        return bytes([CAL.REPLY | len(data), parameter]) + data

    def __repr__(self):  # pragma: no cover
        return '<%s object: parameter=%r, data=%r>' % (
            self.__class__.__name__, self.parameter, self.data)
