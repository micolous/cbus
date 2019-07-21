#!/usr/bin/env python
# cbus/protocol/cal/extended.py - Extended status CAL
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

import abc
from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence, Union

from cbus.common import CAL, ExtendedCALType, Application, GroupState

__all__ = [
    'ExtendedCAL',
    'StatusReport',
    'BinaryStatusReport',
]


class StatusReport(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def decode(cls, data: bytes) -> StatusReport:
        raise NotImplementedError('decode')

    @property
    @abc.abstractmethod
    def block_type(self) -> ExtendedCALType:
        raise NotImplementedError('block_type')

    @abc.abstractmethod
    def encode(self) -> bytes:
        raise NotImplementedError('encode')


@dataclass
class BinaryStatusReport(StatusReport, Sequence[GroupState]):
    _group_states: Sequence[GroupState]

    def __getitem__(self, i: int) -> GroupState:
        return self._group_states[i]

    def __len__(self) -> int:
        return len(self._group_states)

    def __iter__(self) -> Iterator[GroupState]:
        return iter(self._group_states)

    @classmethod
    def decode(cls, data: bytes) -> BinaryStatusReport:
        states = []
        for c in data:
            states += [
                GroupState(c & 0x3),
                GroupState((c >> 2) & 0x03),
                GroupState((c >> 4) & 0x03),
                GroupState((c >> 6) & 0x03)]

        return BinaryStatusReport(states)

    @property
    def block_type(self) -> ExtendedCALType:
        return ExtendedCALType.BINARY

    def encode(self) -> bytes:
        group_states = list(self._group_states)
        r = len(group_states) % 4
        if r != 0:
            # add padding
            group_states += [GroupState.MISSING] * (4 - r)

        # iterate 4 groups at a time
        o = []
        for p in range(0, len(group_states), 4):
            o.append(group_states[p] |
                     (group_states[p + 1] << 2) |
                     (group_states[p + 2] << 4) |
                     (group_states[p + 3] << 6))

        return bytes(o)


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
            CAL.EXTENDED_STATUS | (len(report) + 1),
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
        else:
            raise NotImplementedError('block_type = {:x}'.format(block_type))

        return ExtendedCAL(
            externally_initiated, child_application, block_start, report)
