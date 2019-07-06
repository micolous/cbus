#!/usr/bin/env python
# cbus/protocol/confirm_packet.py - PCI Confirmation parket
# Copyright 2012-2019 Michael Farrell <micolous+git@gmail.com>
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

    def __init__(self, code, success):
        super(ConfirmationPacket, self).__init__()

        self.code = code
        if self.code not in CONFIRMATION_CODES:
            raise ValueError('confirmation code is not valid')

        self.success = bool(success)

    def encode(self, source_addr=None) -> bytes:
        return self.code + (b'.' if self.success else b'#')
