#!/usr/bin/env python
# cbus/protocol/cal/report.py - Status report types
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
from typing import Iterator, Sequence

from cbus.common import ExtendedCALType, GroupState

__all__ = [
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
