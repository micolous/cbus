#!/usr/bin/env python
# cbus/protocol/cal/recall.py - recall parameter
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

from cbus.common import CAL

__all__ = [
    'RecallCAL',
]


@dataclass
class RecallCAL:
    """
    Recall CAL request.

    Ref: Serial Interface Guide, s7.1

    """
    param: int
    count: int

    @classmethod
    def decode_cal(cls, data: bytes) -> Tuple[RecallCAL, int]:
        """
        Decodes identify SAL.
        """

        return RecallCAL(data[1], data[2]), 3

    def encode(self) -> bytes:
        return bytes([CAL.RECALL, self.param & 0xff, self.count & 0xff])
