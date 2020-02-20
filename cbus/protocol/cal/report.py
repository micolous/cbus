#!/usr/bin/env python
# cbus/protocol/cal/report.py - Status report types
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

import abc
from dataclasses import dataclass
from typing import Iterator, Optional, Sequence

from cbus.common import ExtendedCALType, GroupState

__all__ = [
    'StatusReport',
    'BinaryStatusReport',
    'LevelStatusReport',
    'manchester_decode',
    'manchester_encode',
]

_MANCHESTER_NIBBLES = (0b1010, 0b1001, 0b0110, 0b0101)  # 0xa, 0x9, 0x6, 0x5


def manchester_decode(b: bytes) -> Optional[int]:
    try:
        n0 = _MANCHESTER_NIBBLES.index(b[0] & 0xf)
        n1 = _MANCHESTER_NIBBLES.index(b[0] >> 4)
        n2 = _MANCHESTER_NIBBLES.index(b[1] & 0xf)
        n3 = _MANCHESTER_NIBBLES.index(b[1] >> 4)
    except ValueError:
        return None

    return n0 | n1 << 2 | n2 << 4 | n3 << 6


def manchester_encode(value: Optional[int],
                      buf: Optional[bytearray] = None,
                      off: int = 0):
    if buf is None:
        buf = bytearray(2)
    if len(buf) < off + 2:
        raise IndexError(f'buf too small, need {off+2} bytes')
    if value is None:
        return buf

    value = int(value) & 0xff
    buf[off] = (_MANCHESTER_NIBBLES[value & 0x3] |
                _MANCHESTER_NIBBLES[value >> 2 & 0x3] << 4)
    buf[off + 1] = (_MANCHESTER_NIBBLES[value >> 4 & 0x3] |
                    _MANCHESTER_NIBBLES[value >> 6 & 0x3] << 4)
    return buf


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
class LevelStatusReport(StatusReport, Sequence[Optional[int]]):
    """
    Level Status Report, described in Serial Interface Guide p48-49.

    Warning: this is probably the single-strangest part of the C-Bus Protocol.

    Each level consists of 2 bytes of data, encoding a 8-bit value. Each
    nibble represents 2 _bits_ of state _only_:

    * 0xA => 00
    * 0x9 => 01
    * 0x6 => 10
    * 0x5 => 11

    For example:

    * 0xAAAA => Level 0xFF (full on)
    * 0x9599 => Level 0x57
    * 0x5555 => Level 0x00 (full off)
    * 0x0000 => Group address is missing / unassigned

    The guide states that nibbles other than 0xA, 0x9, 0x6 and 0x5 indicate
    some noise on the transmission, or units with the same group address but
    different level state.

    I suspect that the reason for this strangeness is because this coding is
    leaking information out of the analogue domain of the __actual__ C-Bus
    wire protocol.

    If you compare the nibbles you get on serial with their __direct__ binary
    representation, as well as the final coding:

    * 0xA (10 10) => 00
    * 0x9 (10 01) => 01
    * 0x6 (01 10) => 10
    * 0x5 (01 01) => 11

    This would indicate that each "0" bit is encoded as "high-low", and each
    "1" bit is encoded as "low-high" -- which sounds like IEEE 802.3-style
    Manchester coding.

    Under the hood, it's likely that every unit tries to transmit its state
    in response to this query in synchronisation, and if a unit is missing,
    the signal level stays low (ie: 00).

    """
    _group_states: Sequence[Optional[int]]

    def __getitem__(self, i: int) -> Optional[int]:
        return self._group_states[i]

    def __len__(self) -> int:
        return len(self._group_states)

    def __iter__(self) -> Iterator[Optional[int]]:
        return iter(self._group_states)

    @classmethod
    def decode(cls, data: bytes) -> LevelStatusReport:
        states = []
        if len(data) % 2 != 0:
            raise ValueError(
                'Expected a multiple of 2 bytes in LevelStatusReport')

        for o in range(0, len(data), 2):
            states.append(manchester_decode(data[o:o+2]))

        return LevelStatusReport(states)

    @property
    def block_type(self) -> ExtendedCALType:
        return ExtendedCALType.LEVEL

    def encode(self) -> bytes:
        group_states = list(self._group_states)

        o = bytearray(len(group_states) * 2)
        for i, state in enumerate(group_states):
            manchester_encode(state, o, i * 2)

        return bytes(o)
