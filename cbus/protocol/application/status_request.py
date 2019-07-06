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

from typing import FrozenSet, List

from cbus.common import Application
from cbus.protocol.application.sal import BaseApplication, SAL


_LEVEL_REQUEST = b'\x73\x07'
_SUPPORTED_APPLICATIONS = frozenset({int(Application.STATUS_REQUEST)})


class StatusRequestApplication(BaseApplication):
    @staticmethod
    def supported_applications() -> FrozenSet[int]:
        return _SUPPORTED_APPLICATIONS

    @staticmethod
    def decode_sals(data: bytes) -> List[SAL]:
        return [StatusRequestSAL(data)]


class StatusRequestSAL(SAL):
    def __init__(self, data: bytes):
        # TODO: implement parameters to generate these properly
        if data[0] in (0x7a, 0xfa):
            # 0x7a version of the status request (binary on/off states)
            # 0xfa version is deprecated and "shouldn't be used". But it
            # totally still is...
            data = data[1:]
            self.level_request = False
        elif data.startswith(_LEVEL_REQUEST):
            # 7307 version of the status request (levels, in v4)
            data = data[2:]
            self.level_request = True
        else:
            raise NotImplementedError(
                'Unknown status request type {}'.format(data[0]))

        # Application that the status request is about
        self.child_application = data[0]
        self.group_address = data[1]

        if self.group_address & 0x1f != 0:
            raise ValueError(
                'group_address report must be a multiple of 0x20')

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
