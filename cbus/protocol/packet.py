#!/usr/bin/env python
# cbus/protocol/packet.py - Extensible protocol library for encoding and
#                           decoding PCI protocol data.
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

from base64 import b16encode, b16decode
from cbus.protocol.reset_packet import ResetPacket
from cbus.protocol.base_packet import BasePacket
#from cbus.protocol.pp_packet import PointToPointPacket
#from cbus.protocol.ppm_packet import PointToPointToMultipointPacket
from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.dm_packet import DeviceManagementPacket
from cbus.common import *
import warnings

def decode_packet(data, checksum=True, strict=True, server_packet=False):
	data = data.strip()
	
	# determine if this is a hard reset
	if not server_packet and data == '~~~':
		# reset
		return ResetPacket()

	# get the checksum, if it's there.
	if checksum:
		# check the checksum
		if not validate_cbus_checksum(data):
			if strict:
				raise ValueError, "C-Bus checksum incorrect and strict mode is enabled: %r." % data
			else:
				warnings.warn("C-Bus checksum failure in data %r" % data, UserWarning)
		
		# strip checksum
		data = data[:-2]
	
	if data[0] == '\\':
		data = data[1:]
	
	for c in data:
		if c not in HEX_CHARS:
			raise ValueError, "Non-base16 input: %r in %r" % (c, data)
	
	# base16 decode
	data = b16decode(data)
	
	# flags (serial interface guide s3.4)
	flags = ord(data[0])
	
	destination_address_type = flags & 0x07
	# "reserved", "must be set to 0"
	rc = (flags & 0x18) >> 3
	dp = (flags & 0x20) == 0x20
	# priority class
	priority_class = (flags & 0xC0) >> 6
	
	# increment ourselves along
	data = data[1:]
	
	# TODO: handle source address
	
	
	if dp:
		# device management flag set!
		# this is used to set parameters of the PCI
		return DeviceManagementPacket.decode_packet(data, checksum, flags, destination_address_type, rc, dp, priority_class)
	
	
	if destination_address_type == DAT_PP:
		# decode as point-to-point packet
		#return PointToPointPacket.decode_packet(data, checksum, flags, destination_address_type, rc, dp, priority_class)
		pass
	elif destination_address_type == DAT_PM:
		# decode as point-to-multipoint packet
		return PointToMultipointPacket.decode_packet(data, checksum, flags, destination_address_type, rc, dp, priority_class)
	elif destination_address_type == DAT_PPM:
		# decode as point-to-point-to-multipoint packet
		#return PointToPointToMultipointPacket.decode_packet(data, checksum, flags, destination_address_type, rc, dp, priority_class)
		pass


