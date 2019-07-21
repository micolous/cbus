#!/usr/bin/env python
# cbus/protocol/cal/identify.py - Identify unit
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
from typing import Tuple

from cbus.common import CAL, IdentifyAttribute

__all__ = [
    'IdentifyCAL',
]


@dataclass
class IdentifyCAL:
    """
    Identify CAL request.

    Ref: Serial Interface Guide, s7.1

    """
    attribute: IdentifyAttribute

    @classmethod
    def decode_cal(cls, data: bytes) -> Tuple[IdentifyCAL, int]:
        """
        Decodes identify SAL.
        """

        return IdentifyCAL(IdentifyAttribute(data[1])), 2

    def encode(self) -> bytes:
        return bytes([CAL.IDENTIFY, self.attribute & 0xff])
