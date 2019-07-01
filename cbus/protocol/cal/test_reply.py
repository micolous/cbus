#!/usr/bin/env python
# cbus/protocol/cal/test_reply.py - Reply CAL unit test
# Copyright 2013 Michael Farrell <micolous+git@gmail.com>
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

from cbus.protocol.packet import decode_packet
from cbus.protocol.pp_packet import PointToPointPacket
from cbus.protocol.cal.reply import *
from cbus.common import *


def S9_2_Test():
    "Example in s9.2 (Serial Interface Guide) of decoding a reply CAL"
    p, r = decode_packet('8604990082300328', server_packet=True)
    assert isinstance(p, PointToPointPacket), 'Packet is not PointToPointPacket'
    assert p.source_address == 4
    assert p.unit_address == 0x99
    assert len(p.cal) == 1

    assert isinstance(p.cal[0], ReplyCAL)
    assert p.cal[0].parameter == 0x30
    assert p.cal[0].data == '\x03'

    assert p.encode() == '8604990082300328'
