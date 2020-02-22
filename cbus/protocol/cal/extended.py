#!/usr/bin/env python
# cbus/protocol/cal/extended.py - Extended status CAL
# Copyright 2019-2020 Michael Farrell <micolous+git@gmail.com>
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
from typing import Union

from cbus.common import CAL, ExtendedCALType, Application
from cbus.protocol.cal.report import (
    StatusReport, BinaryStatusReport, LevelStatusReport)

__all__ = [
    'ExtendedCAL',
]


@dataclass
class ExtendedCAL:
    """

    """
    externally_initated: bool
    child_application: Union[Application, int]
    block_start: int
    report: StatusReport

    @property
    def coding_byte(self) -> int:
        return ((0x40 if self.externally_initated else 0) |
                (self.report.block_type & 0x7))

    def encode(self) -> bytes:
        report = self.report.encode()

        return bytes([
            CAL.EXTENDED_STATUS | (len(report) + 3),
            self.coding_byte,
            self.child_application & 0xff,
            self.block_start & 0xff]) + report

    @classmethod
    def decode_cal(cls, data: bytes) -> ExtendedCAL:
        # expects an extended status cal, cropped to exact size, starting
        # from the coding byte
        externally_initiated = (data[0] & 0x40) > 0
        block_type = data[0] & 0x7
        child_application = data[1]
        block_start = data[2]
        payload = data[3:]

        if block_type == ExtendedCALType.BINARY:
            report = BinaryStatusReport.decode(payload)
        elif block_type == ExtendedCALType.LEVEL:
            report = LevelStatusReport.decode(payload)
        else:
            raise NotImplementedError('block_type = {:x}'.format(block_type))

        return ExtendedCAL(
            externally_initiated, child_application, block_start, report)
