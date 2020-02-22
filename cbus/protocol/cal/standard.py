#!/usr/bin/env python
# cbus/protocol/cal/standard.py - Standard status CAL
# Copyright 2019 Michael Farrell <micolous+git@gmail.com>
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
from dataclasses import dataclass
from typing import Union

from cbus.common import CAL, Application, add_cbus_checksum
from cbus.protocol.cal.report import BinaryStatusReport
from cbus.protocol.base_packet import SpecialServerPacket

__all__ = [
    'StandardCAL',
]


@dataclass
class StandardCAL(SpecialServerPacket):
    """

    """
    child_application: Union[Application, int]
    block_start: int
    report: BinaryStatusReport

    # Only used if encoding packets
    checksum: bool = True

    def encode(self) -> bytes:
        report = self.report.encode()

        return bytes([
            CAL.STANDARD_STATUS | (len(report) + 3),
            self.child_application & 0xff,
            self.block_start & 0xff]) + report

    def encode_packet(self) -> bytes:
        """
        Standard CALs can be also sent as a packet without headers directly
        onto the network.

        This adds a checksum (if checksum=True) and base16 encodes the CAL
        like it was a normal packet.
        """
        # checksum it, if needed.
        p = self.encode()

        if self.checksum:
            p = add_cbus_checksum(p)

        return b16encode(p)

    @classmethod
    def decode_cal(cls, data: bytes) -> StandardCAL:
        # expects a standard status cal, cropped to exact size, starting
        # from the application byte
        child_application = data[0]
        block_start = data[1]
        payload = data[2:]

        report = BinaryStatusReport.decode(payload)

        return StandardCAL(child_application, block_start, report)
