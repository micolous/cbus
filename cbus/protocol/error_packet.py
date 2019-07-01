#!/usr/bin/env python
# cbus/protocol/error_packet.py - PCI Error parket
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

__all__ = ['PCIErrorPacket']


class PCIErrorPacket(SpecialServerPacket):

    def __init__(self):
        super(PCIErrorPacket, self).__init__()

    def encode(self, source_addr=None):
        return b'!'
