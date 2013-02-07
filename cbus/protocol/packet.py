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
from cbus.protocol.scs_packet import SmartConnectShortcutPacket
from cbus.protocol.base_packet import BasePacket
from cbus.protocol.pp_packet import PointToPointPacket
#from cbus.protocol.ppm_packet import PointToPointToMultipointPacket
from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.dm_packet import DeviceManagementPacket
from cbus.protocol.po_packet import PowerOnPacket
from cbus.protocol.error_packet import PCIErrorPacket
from cbus.protocol.confirm_packet import ConfirmationPacket
from cbus.common import *
import warnings

def decode_packet(data, checksum=True, strict=True, server_packet=True):
	"""
	Decodes a packet from or send to the PCI.
	
	Returns a tuple, the packet that was parsed and the remainder that was
	unparsed (in the case of some special commands.
	
	If no packet was able to be parsed, the first element of the tuple will be
	None.  However there may be some circumstances where there is still a
	remainder to be parsed (cancel request).
	
	"""
	data = data.strip()
	if data == '':
		return None, None
	
	# packets from clients have some special flags which we need to handle.
	if server_packet:
		if data[0] == '+':
			data = data[1:]
			return PowerOnPacket(), data
		elif data[0] == '!':
			# buffer is full / invalid checksum, some requests may be dropped.
			# serial interface guide s4.3.3 p28
			data = data[1:]
			return PCIErrorPacket(), data
		
		if data[0] in CONFIRMATION_CODES:
			success = data[1] == '.'
			code = data[0]
			data = data[2:]
			return ConfirmationPacket(code, success), data
			
			
			
	else:
		if data == '~~~':
			# reset
			return ResetPacket(), None
		elif data == '|':
			# smart + connect shortcut
			return SmartConnectShortcutPacket(), None
		elif '?' in data:
			# discard data before the ?, and resubmit for processing.
			data = data.split('?')[-1]
			return None, data

		if data[0] == '\\':
			data = data[1:]
		
		if data[0] == '@':
			# this causes it to be once-off a "basic" mode command.
			data = data[1:]
			checksum = False		
			
		if data[-1] not in HEX_CHARS:
			# then there is a confirmation code at the end.
			confirmation = data[-1]
			
			if confirmation not in CONFIRMATION_CODES:
				if strict:
					raise ValueError, "Confirmation code is not a lowercase letter in g - z"
				else:
					warnings.warn('Confirmation code is not a lowercase letter in g - z')
					
			data = data[:-1]
		else:
			confirmation = None
			
			
	for c in data:
		if c not in HEX_CHARS:
			raise ValueError, "Non-base16 input: %r in %r" % (c, data)
			
	# get the checksum, if it's there.
	if checksum:
		# check the checksum
		if not validate_cbus_checksum(data):
			real_checksum = get_real_cbus_checksum(data)
			if strict:
				raise ValueError, "C-Bus checksum incorrect (expected %r) and strict mode is enabled: %r." % (real_checksum, data)
			else:
				warnings.warn("C-Bus checksum incorrect (expected %r) in data %r" % (real_checksum, data), UserWarning)
		
		# strip checksum
		data = data[:-2]
	
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
	
	# handle source address
	if server_packet:
		source_addr = ord(data[0])
		data = data[1:]
	else:
		source_addr = None
	
	if dp:
		# device management flag set!
		# this is used to set parameters of the PCI
		p = DeviceManagementPacket.decode_packet(data, checksum, flags, destination_address_type, rc, dp, priority_class)
	
	
	elif destination_address_type == DAT_PP:
		# decode as point-to-point packet
		p = PointToPointPacket.decode_packet(data, checksum, flags, destination_address_type, rc, dp, priority_class)
		#raise NotImplementedError, 'Point-to-point'
	elif destination_address_type == DAT_PM:
		# decode as point-to-multipoint packet
		p = PointToMultipointPacket.decode_packet(data, checksum, flags, destination_address_type, rc, dp, priority_class)
	elif destination_address_type == DAT_PPM:
		# decode as point-to-point-to-multipoint packet
		#return PointToPointToMultipointPacket.decode_packet(data, checksum, flags, destination_address_type, rc, dp, priority_class)
		raise NotImplementedError, 'Point-to-point-tomultipoint'

	if not server_packet and confirmation:
		p.confirmation = confirmation
		p.source_address = None
	elif source_addr:
		p.source_address = source_addr
		p.confirmation = None
	
	return p, None

