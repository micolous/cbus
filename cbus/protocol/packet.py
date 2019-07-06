#!/usr/bin/env python
# cbus/protocol/packet.py - Extensible protocol library for encoding and
#                           decoding PCI protocol data.
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

from base64 import b16decode
from six import byte2int, indexbytes, int2byte
import warnings

from cbus.protocol.reset_packet import ResetPacket
from cbus.protocol.scs_packet import SmartConnectShortcutPacket
from cbus.protocol.base_packet import InvalidPacket
from cbus.protocol.pp_packet import PointToPointPacket
# from cbus.protocol.ppm_packet import PointToPointToMultipointPacket
from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.dm_packet import DeviceManagementPacket
from cbus.protocol.po_packet import PowerOnPacket
from cbus.protocol.error_packet import PCIErrorPacket
from cbus.protocol.confirm_packet import ConfirmationPacket
from cbus.common import (
    DestinationAddressType, PriorityClass,
    HEX_CHARS, CONFIRMATION_CODES, END_COMMAND,
    END_RESPONSE, get_real_cbus_checksum, validate_cbus_checksum)


def decode_packet(data, checksum=True, strict=True, server_packet=True):
    """
    Decodes a packet from or send to the PCI.

    Returns a tuple, the packet that was parsed and the buffer position we
    parsed up to.

    If no packet was able to be parsed, the first element of the tuple will be
    None.  However there may be some circumstances where there is still a
    remainder to be parsed (cancel request).

    :type data: bytes
    :type checksum: bool
    :type strict: bool
    :type server_packet: bool
    :rtype: Pair[Optional[BasePacket], int]
    """
    confirmation = None
    consumed = 0

    if data == b'':
        return None, 0

    # packets from clients have some special flags which we need to handle.
    if server_packet:
        if data.startswith(b'+'):  # +
            return PowerOnPacket(), consumed + 1
        elif data.startswith(b'!'):  # !
            # buffer is full / invalid checksum, some requests may be dropped.
            # serial interface guide s4.3.3 p28
            return PCIErrorPacket(), consumed + 1

        if data[0] in CONFIRMATION_CODES:
            success = indexbytes(data, 1) == 0x2e  # .
            code = byte2int(data)
            return ConfirmationPacket(code, success), consumed + 2

        end = data.find(END_RESPONSE)
    else:
        if data.startswith(b'~'):
            # Reset
            # Serial Interface Guide, s4.2.3
            return ResetPacket(), consumed + 1
        elif data.startswith(b'|' + END_COMMAND):
            # SMART + CONNECT shortcut
            consumed += 1 + len(END_COMMAND)
            return SmartConnectShortcutPacket(), consumed
        else:
            # Check if we need to discard a message
            # Serial interface guide, s4.2.4
            nlp = data.find(END_COMMAND)
            qp = data.find(b'?')
            if -1 < qp < nlp:
                # Discard data before the "?", and continue
                return None, consumed + qp + 1

        end = data.find(END_COMMAND)

    # Look for ending character(s). If there is none, break out now.
    if end == -1:
        return None, consumed

    # Make it so the end of the buffer is where the end of the command is, and
    # consume the command up to and including the ending byte(s).
    data = data[:end]

    if server_packet:
        consumed += end + len(END_RESPONSE)
    else:
        consumed += end + len(END_COMMAND)

    if not data:
        # Empty command, break out!
        return None, consumed

    if not server_packet:
        if data.startswith(b'@'):
            # Once-off BASIC mode command, Serial Interface Guide, s4.2.7
            checksum = False
            data = data[1:]
        elif data.startswith(b'\\'):
            data = data[1:]

        if data[-1] not in HEX_CHARS:
            # then there is a confirmation code at the end.
            confirmation = int2byte(indexbytes(data, -1))

            if confirmation not in CONFIRMATION_CODES:
                if strict:
                    return InvalidPacket(data, ValueError(
                        'Confirmation code is not in range g..z')), consumed
                else:
                    warnings.warn(
                        'Confirmation code is not in range g..z')

            # strip confirmation byte
            data = data[:-1]

    for c in data:
        if c not in HEX_CHARS:
            return InvalidPacket(data, ValueError(
                'Non-base16 input: {} in {}'.format(c, data))), consumed

    # get the checksum, if it's there.
    if checksum:
        # check the checksum
        if not validate_cbus_checksum(data):
            real_checksum = get_real_cbus_checksum(data)
            if strict:
                return InvalidPacket(data, ValueError(
                    'C-Bus checksum incorrect (expected {}) and strict mode '
                    'is enabled: {}'.format(real_checksum, data))), consumed
            else:
                warnings.warn(
                    'C-Bus checksum incorrect (expected {}) in data '
                    '{}'.format(real_checksum, data), UserWarning)

        # strip checksum
        data = data[:-2]

    # base16 decode
    data = b16decode(data)

    # flags (serial interface guide s3.4)
    flags = byte2int(data)

    destination_address_type = DestinationAddressType(flags & 0x07)
    # "reserved", "must be set to 0"
    rc = (flags >> 3) & 0x03
    dp = (flags & 0x20) == 0x20
    # priority class
    priority_class = PriorityClass((flags >> 6) & 0x03)

    # increment ourselves along
    data = data[1:]

    # handle source address
    if server_packet:
        source_addr = byte2int(data)
        data = data[1:]
    else:
        source_addr = None

    if dp:
        # device management flag set!
        # this is used to set parameters of the PCI
        p = DeviceManagementPacket.decode_packet(
            data=data, checksum=checksum, priority_class=priority_class)

    elif destination_address_type == DestinationAddressType.POINT_TO_POINT:
        # decode as point-to-point packet
        p = PointToPointPacket.decode_packet(
            data=data, checksum=checksum, priority_class=priority_class)
    elif destination_address_type == DestinationAddressType.POINT_TO_MULTIPOINT:
        # decode as point-to-multipoint packet
        p = PointToMultipointPacket.decode_packet(
            data=data, checksum=checksum, priority_class=priority_class)
    elif (destination_address_type ==
          DestinationAddressType.POINT_TO_POINT_TO_MULTIPOINT):
        # decode as point-to-point-to-multipoint packet
        # return PointToPointToMultipointPacket.decode_packet(data, checksum,
        # flags, destination_address_type, rc, dp, priority_class)
        raise NotImplementedError('Point-to-point-to-multipoint')

    if not server_packet:
        p.confirmation = confirmation
        p.source_address = None
    elif source_addr:
        p.source_address = source_addr
        p.confirmation = None

    return p, consumed
