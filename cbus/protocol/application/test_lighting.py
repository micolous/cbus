#!/usr/bin/env python
# cbus/protocol/application/test_lighting.py - Lighting Application unit tests
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
from cbus.protocol.application.lighting import *
from cbus.common import *

def S6_4_Test():
	"Examples in serial interface guide, s6.4"
	# Switch on light at GA 8
	p, r = decode_packet('\\0538000108BAg', server_packet=False)
	
	assert isinstance(p, PointToMultipointPacket)
	assert len(p.sal) == 1
	
	assert isinstance(p.sal[0], LightingOffSAL)
	assert p.sal[0].group_address == 8
	
	# check that it encodes properly again
	assert p.encode() == '0538000108BA'
	assert p.confirmation == 'g'
	
	# concatenated packet
	p, r = decode_packet('\\05380001087909090A25h', server_packet=False)
	
	assert isinstance(p, PointToMultipointPacket)
	assert len(p.sal) == 3
	
	# turn off light 8
	assert isinstance(p.sal[0], LightingOffSAL)
	assert p.sal[0].group_address == 8
	
	# turn on light 9		
	assert isinstance(p.sal[1], LightingOnSAL)
	assert p.sal[1].group_address == 9
	
	# terminate ramp on light 10)
	assert isinstance(p.sal[2], LightingTerminateRampSAL)
	assert p.sal[2].group_address == 10
	
	# check that it encodes properly again
	assert p.encode() == '05380001087909090A25'
	assert p.confirmation == 'h'
		

def S2_11_Test():
	"Examples in Lighting Application s2.11"
	# switch on light at GA 0x93
	p, r = decode_packet('\\0538007993B7j', server_packet=False)
	
	assert isinstance(p, PointToMultipointPacket)
	assert len(p.sal) == 1
	
	assert isinstance(p.sal[0], LightingOnSAL)
	assert p.sal[0].group_address == 0x93
	
	# check that it encodes properly again
	assert p.encode() == '0538007993B7'
	assert p.confirmation == 'j'


def S9_1_Test():
	"Examples in quick start guide, s9.1"
	# turn on light 0x21
	p, r = decode_packet('\\053800792129i', server_packet=False)
	
	assert isinstance(p, PointToMultipointPacket)
	assert len(p.sal), 1
	
	assert isinstance(p.sal[0], LightingOnSAL)
	assert p.sal[0].group_address, 0x21

	# check that it encodes properly again
	assert p.encode(), '053800792129'
	assert p.confirmation, 'i'
	
	# turn off light 0x21
	p, r = decode_packet('\\0538000121A1k', server_packet=False)
	
	assert isinstance(p, PointToMultipointPacket)
	assert len(p.sal) == 1
	
	assert isinstance(p.sal[0], LightingOffSAL)
	assert p.sal[0].group_address == 0x21

	# check that it encodes properly again
	assert p.encode() == '0538000121A1'
	assert p.confirmation == 'k'
	
	# ramp light 0x21 to 50% over 4 seconds
	p, r = decode_packet('\\0538000A217F19l', server_packet=False)
	
	assert isinstance(p, PointToMultipointPacket)
	assert len(p.sal) == 1
	
	assert isinstance(p.sal[0], LightingRampSAL)
	assert p.sal[0].group_address == 0x21
	assert p.sal[0].duration == 4
	# rounding must be done to 2 decimal places, as the value isn't actually
	# 50%, but 49.8039%.  next value is 50.1%.
	assert round(p.sal[0].level, 2) == 0.5
	
	# check that it encodes properly again
	assert p.encode() == '0538000A217F19'		
	assert p.confirmation == 'l'


def lighting_encode_decode_test():
	"self-made tests of encode then decode"
	
	orig = PointToMultipointPacket(application=APP_LIGHTING)
	orig.source_address = 5
	orig.sal.append(LightingOnSAL(orig, 27))
	
	data = orig.encode()

	d, r = decode_packet(data)
	assert isinstance(orig, PointToMultipointPacket)		
	assert orig.source_address == d.source_address
	assert len(orig.sal) == len(d.sal)
	
	assert isinstance(d.sal[0], LightingOnSAL)
	assert orig.sal[0].group_address == d.sal[0].group_address
	
	# ensure there is no remaining data to be parsed
	assert r == None


def lighting_encode_decode_client_test():
	"self-made tests of encode then decode, with packets from a client."
	
	orig = PointToMultipointPacket(application=APP_LIGHTING)
	orig.sal.append(LightingOnSAL(orig, 27))
	
	data = orig.encode()

	d, r = decode_packet(data, server_packet=False)
	assert isinstance(orig, PointToMultipointPacket)		
	assert len(orig.sal) == len(d.sal)
	
	assert isinstance(d.sal[0], LightingOnSAL)
	assert orig.sal[0].group_address == d.sal[0].group_address
	
	# ensure there is no remaining data to be parsed
	assert r == None
	
def issue2_test():
	"Handle the null lighting packet described in Issue #2."
	# lighting packet from the server, lighting application, source address 0x06
	# sometimes cbus units emit these null lighting commands because of an off-by-one issue?
	p, r = decode_packet('05063800BD')
	
	assert isinstance(p, PointToMultipointPacket)
	assert p.application == 0x38
	assert p.source_address == 0x06
	assert len(p.sal) == 0
	
	assert r == None
