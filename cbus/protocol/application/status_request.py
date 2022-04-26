#!/usr/bin/env python3
# cbus/protocol/application/status_request.py
# Status Request pseudo-application
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

from dataclasses import dataclass
from typing import FrozenSet, Sequence
import warnings

from cbus.common import Application
from cbus.protocol.application.sal import BaseApplication, SAL


_LEVEL_REQUEST = b'\x73\x07'
_SUPPORTED_APPLICATIONS = frozenset({int(Application.STATUS_REQUEST)})


class StatusRequestApplication(BaseApplication):
    @staticmethod
    def supported_applications() -> FrozenSet[int]:
        return _SUPPORTED_APPLICATIONS

    @staticmethod
    def decode_sals(data: bytes,_=None) -> Sequence[SAL]:
        return StatusRequestSAL.decode_sals(data)


@dataclass
class StatusRequestSAL(SAL):
    level_request: bool
    group_address: int
    child_application: int

    @classmethod
    def decode_sals(cls, data: bytes,_=None) -> Sequence[StatusRequestSAL]:
        output = []

        while data:
            if data[0] in (0x7a, 0xfa):
                # 0x7a version of the status request (binary on/off states)
                # 0xfa version is deprecated and "shouldn't be used". But it
                # totally still is...
                data = data[1:]
                level_request = False
            elif data.startswith(_LEVEL_REQUEST):
                # 7307 version of the status request (levels, in v4)
                data = data[2:]
                level_request = True
            else:
                raise NotImplementedError(
                    'Unknown status request type 0x{:x}'.format(data[0]))

            if len(data) < 2:
                # not enough data to go on
                warnings.warn(
                    'Got incomplete SAL for status request application'
                    '(malformed packet)', UserWarning)

            # Application that the status request is about
            child_application = data[0]
            group_address = data[1]
            data = data[2:]

            if group_address & 0x1f != 0:
                raise ValueError(
                    'group_address report must be a multiple of 0x20')

            output.append(StatusRequestSAL(
                level_request, group_address, child_application))

        return output

    @property
    def application(self) -> Application:
        return Application.STATUS_REQUEST

    def encode(self) -> bytes:
        child_application = int(self.child_application) & 0xff
        group_address = self.group_address & 0xe0
        level_request = bool(self.level_request)

        if level_request:
            return _LEVEL_REQUEST + bytes([child_application, group_address])
        else:
            return bytes([0x7a, child_application, group_address])
