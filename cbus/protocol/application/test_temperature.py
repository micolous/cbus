#!/usr/bin/env python
# cbus/protocol/application/test_temperature.py - Temperature broadcast unit tests
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
from cbus.protocol.application.temperature import *
from cbus.common import *

def S9_11_Test():
	"Example in temperature broadcast application guide, s9.11"
	# Temperature of 25 degrees at group 5
	# note, the guide actually states that there is a checksum, but no
	# checksum is actually on the packet!
	p, r = decode_packet('\\05190002056477g', server_packet=False)
	
	assert isinstance(p, PointToMultipointPacket)
	assert len(p.sal) == 1

	assert isinstance(p.sal[0], TemperatureBroadcastSAL)
	assert p.sal[0].group_address == 5
	assert p.sal[0].temperature == 25
	
	## check that it encodes properly again
	assert p.encode() == '05190002056477'
	assert p.confirmation == 'g'

def temperature_encode_decode_test():
	"self-made tests of encode then decode"
	
	orig = PointToMultipointPacket(application=APP_TEMPERATURE)
	orig.source_address = 5
	orig.sal.append(TemperatureBroadcastSAL(orig, 10, 0.5))
	orig.sal.append(TemperatureBroadcastSAL(orig, 11, 56))
	
	data = orig.encode()

	d, r = decode_packet(data)
	assert isinstance(orig, PointToMultipointPacket)		
	assert orig.source_address == d.source_address
	assert len(orig.sal) == len(d.sal)
	
	for x in range(len(d.sal)):
		assert isinstance(d.sal[x], TemperatureBroadcastSAL)
		assert orig.sal[x].group_address == d.sal[x].group_address
		assert orig.sal[x].temperature == d.sal[x].temperature
	
	# ensure there is no remaining data to be parsed
	assert r == None
