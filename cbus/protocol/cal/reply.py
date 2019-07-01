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
from six import byte2int, indexbytes, int2byte, iterbytes

from cbus.common import CAL_RES_REPLY

__all__ = [
    'ReplyCAL',
]


class ReplyCAL(object):
    """
    Reply cal

    TODO: No way at the moment to tell between responses to RECALL,
          GETSTATUS and IDENTIFY?
    """

    def __init__(self, packet, parameter, data):
        self.packet = packet
        self.parameter = parameter
        self.data = data

    @classmethod
    def decode_cal(cls, data, packet):
        """
        Decodes reply CAL.
        """

        cal = ReplyCAL(packet, byte2int(data), data[1:])

        return cal

    def encode(self):
        if self.parameter < 0 or self.parameter > 0xff:
            raise ValueError('parameter must be in range 0..255')
        if len(self.data) >= 0x1f:
            raise ValueError('must be less than 31 bytes of data')
        return [(CAL_RES_REPLY | (len(self.data) + 1)),
                self.parameter] + list(iterbytes(self.data))

    def __repr__(self):  # pragma: no cover
        return '<%s object: parameter=%r, data=%r>' % (
            self.__class__.__name__, self.parameter, self.data)
