#!/usr/bin/env python3
# cbus/protocol/confirm_packet.py - PCI Confirmation packet
# Copyright 2012-2020 Michael Farrell <micolous+git@gmail.com>
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

from cbus.protocol.base_packet import SpecialServerPacket
from cbus.common import CONFIRMATION_CODES

__all__ = ['ConfirmationPacket']


class ConfirmationPacket(SpecialServerPacket):
    """
    Confirmation special packet.  Serial interface guide s4.3.3.3 p32
    """

    def __init__(self, code: bytes, success: bool):
        super(ConfirmationPacket, self).__init__()

        self._code = code[:1]
        if self._code not in CONFIRMATION_CODES:
            raise ValueError('confirmation code is not valid')

        self._success = bool(success)

    def encode(self) -> bytes:
        return self._code + (b'.' if self._success else b'#')

    @property
    def code(self) -> bytes:
        return self._code

    @property
    def success(self) -> bool:
        return self._success

    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'code={self.code!r}, success={self.success})')
