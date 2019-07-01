#!/usr/bin/env python
# cbus/protocol/application/test_enable.py - Enable control unit tests
# Copyright 2012 Michael Farrell <micolous+git@gmail.com>
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
from cbus.protocol.application.enable import *
from cbus.common import *

def S8_11_Test():
	"Example in enable control application guide, s8.11 (page 7)"
	# Set the network variable 0x37 to 0x82
	p, r = decode_packet('\\05CB0002378275g', server_packet=False)
	
	assert isinstance(p, PointToMultipointPacket)
	assert len(p.sal) == 1

	assert isinstance(p.sal[0], EnableSetNetworkVariableSAL)
	assert p.sal[0].variable == 0x37
	assert p.sal[0].value == 0x82
	
	## check that it encodes properly again
	assert p.encode() == '05CB0002378275'
	assert p.confirmation == 'g'
