#!/usr/bin/env python
# cbus/protocol/test_pm_packet.py - Point to Multipoint packet tests
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

from cbus.protocol.packet import decode_packet
from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.application.lighting import LightingOffSAL


def S4_2_9_2_Test():
    "Serial interface guide s4.2.9.2 (page 23) test"
    # first test
    p, m = decode_packet('\\0538000108BAg', server_packet=False)

    assert isinstance(p, PointToMultipointPacket)
    assert not p.status_request
    assert p.application == 0x38
    assert len(p.sal) == 1

    assert isinstance(p.sal[0], LightingOffSAL)
    assert p.sal[0].group_address == 8

    assert p.confirmation == 'g'

    assert m is None

    # second test
    p, m = decode_packet('\\05FF007A38004Ah', server_packet=False)

    assert isinstance(p, PointToMultipointPacket)
    assert p.status_request
    assert p.application == 0x38
    assert p.group_address == 0
    assert p.confirmation == 'h'

    # no remainder
    assert m is None
