#!/usr/bin/env python3
# cbus/protocol/packet.py - Extensible protocol library for encoding and
#                           decoding PCI protocol data.
# Copyright 2012-2020 Michael Farrell <micolous+git@gmail.com>
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
from typing import Tuple, Union
import warnings

from cbus.protocol.reset_packet import ResetPacket
from cbus.protocol.scs_packet import SmartConnectShortcutPacket
from cbus.protocol.base_packet import BasePacket, InvalidPacket
from cbus.protocol.pp_packet import PointToPointPacket
# from cbus.protocol.ppm_packet import PointToPointToMultipointPacket
from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.dm_packet import DeviceManagementPacket
from cbus.protocol.po_packet import PowerOnPacket
from cbus.protocol.error_packet import PCIErrorPacket
from cbus.protocol.confirm_packet import ConfirmationPacket
from cbus.protocol.cal import AnyCAL
from cbus.common import (
    DestinationAddressType, PriorityClass, MIN_MESSAGE_SIZE,
    HEX_CHARS, CONFIRMATION_CODES, END_COMMAND,
    END_RESPONSE, get_real_cbus_checksum, validate_cbus_checksum)


def decode_packet(
        data: bytes,
        checksum: bool = True,
        strict: bool = True,
        from_pci: bool = True) \
        -> Tuple[Union[BasePacket, AnyCAL, None], int]:
    """
    Decodes a single C-Bus Serial Interface packet.

    The return value is a tuple:

    0. The packet that was parsed, or None if there was no packet that could
       be parsed.
    1. The buffer position that we parsed up to. This may be non-zero even if
       the packet was None (eg: Cancel request).

    Note: this decoder does not support unaddressed packets (such as Standard
    Format Status Replies).

    Note: Direct Command Access causes this method to return AnyCAL instead
    of a BasePacket.

    :param data: The data to parse, in encapsulated serial format.
    :param checksum: If True, requires a checksum for all packets
    :param strict: If True, returns InvalidPacket whenever checksum is
        incorrect. Otherwise, only emits a warning.
    :param from_pci: If True, parses the packet as if it were sent from/by a
        PCI -- if your software was sent packets by a PCI, this is
        what you want.

        If False, this parses the packet as if it were sent to a PCI; parsing
        messages that software expecting to communicate with a PCI sends. This
        could be used to build a fake PCI, or analyse the behaviour of other
        C-Bus software.
    """
    confirmation = None
    consumed = 0
    # Serial Interface User Guide s4.2.7
    device_managment_cal = False

    if data == b'':
        return None, 0

    # There are some special transport-layer flags that need to be handled
    # before parsing the rest of the message.
    if from_pci:
        if data.startswith(b'+'):  # +
            return PowerOnPacket(), consumed + 1
        elif data.startswith(b'!'):  # !
            # buffer is full / invalid checksum, some requests may be dropped.
            # serial interface guide s4.3.3 p28
            return PCIErrorPacket(), consumed + 1

        if len(data) < MIN_MESSAGE_SIZE:
            # Not enough data in the buffer to process yet.
            return None, 0

        if data[0] in CONFIRMATION_CODES:
            success = indexbytes(data, 1) == 0x2e  # .
            code = data[:1]
            return ConfirmationPacket(code, success), consumed + 2

        end = data.find(END_RESPONSE)
    else:
        if data.startswith(b'~'):
            # Reset
            # Serial Interface Guide, s4.2.3
            return ResetPacket(), consumed + 1
        elif data.startswith(b'null'):
            # Toolkit is buggy, just ignore it.
            return None, consumed + 4
        elif (data.startswith(b'|' + END_COMMAND)
              or data.startswith(b'||' + END_COMMAND)):
            # SMART + CONNECT shortcut
            consumed += data.find(END_COMMAND) + 1
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

    if from_pci:
        consumed += end + len(END_RESPONSE)
    else:
        consumed += end + len(END_COMMAND)

    if not data:
        # Empty command, break out!
        return None, consumed

    if not from_pci:
        if data.startswith(b'@'):
            # Once-off BASIC mode command, Serial Interface Guide, s4.2.7
            checksum = False
            device_managment_cal = True
            data = data[1:]
        elif data.startswith(b'\\'):
            data = data[1:]
        else:
            device_managment_cal = True

        if data[-1] not in HEX_CHARS:
            # then there is a confirmation code at the end.
            confirmation = int2byte(indexbytes(data, -1))

            if confirmation not in CONFIRMATION_CODES:
                if strict:
                    return InvalidPacket(
                        payload=data,
                        exception=ValueError(
                            'Confirmation code is not in range g..z')), consumed
                else:
                    warnings.warn(
                        'Confirmation code is not in range g..z')

            # strip confirmation byte
            data = data[:-1]

    for c in data:
        if c not in HEX_CHARS:
            return InvalidPacket(payload=data, exception=ValueError(
                f'Non-base16 input: {c:x} in {data}')), consumed

    # base16 decode
    data = b16decode(data)

    # get the checksum, if it's there.
    if checksum:
        # check the checksum
        if not validate_cbus_checksum(data):
            real_checksum = get_real_cbus_checksum(data)
            if strict:
                return InvalidPacket(payload=data, exception=ValueError(
                    f'C-Bus checksum incorrect (expected 0x{real_checksum:x}) '
                    f'and strict mode is enabled: {data}')), consumed
            else:
                warnings.warn(
                    f'C-Bus checksum incorrect (expected 0x{real_checksum:x}) '
                    f'in data {data}', UserWarning)

        # strip checksum
        data = data[:-1]

    # flags (serial interface guide s3.4)
    flags = byte2int(data)

    try:
        address_type = DestinationAddressType(flags & 0x07)
        # "reserved", "must be set to 0"
        # rc = (flags >> 3) & 0x03
        dp = (flags & 0x20) == 0x20
        # priority class
        priority_class = PriorityClass((flags >> 6) & 0x03)

        # increment ourselves along
        data = data[1:]

        # handle source address
        if from_pci:
            source_addr = byte2int(data)
            data = data[1:]
        else:
            source_addr = None

        if dp:
            # device management flag set!
            # this is used to set parameters of the PCI
            p = DeviceManagementPacket.decode_packet(
                data=data, checksum=checksum, priority_class=priority_class)
        elif device_managment_cal:
            cal, cal_len = PointToPointPacket.decode_cal(data)
            return cal, consumed + cal_len

        elif address_type == DestinationAddressType.POINT_TO_POINT:
            # decode as point-to-point packet
            p = PointToPointPacket.decode_packet(
                data=data, checksum=checksum, priority_class=priority_class)
        elif address_type == DestinationAddressType.POINT_TO_MULTIPOINT:
            # decode as point-to-multipoint packet
            p = PointToMultipointPacket.decode_packet(
                data=data, checksum=checksum, priority_class=priority_class)
        elif (address_type ==
              DestinationAddressType.POINT_TO_POINT_TO_MULTIPOINT):
            # decode as point-to-point-to-multipoint packet
            # return PointToPointToMultipointPacket.decode_packet(data, checksum,
            # flags, destination_address_type, rc, dp, priority_class)
            raise NotImplementedError('Point-to-point-to-multipoint')
        else:
            raise NotImplementedError(
                f'Destination address type = 0x{address_type:x}')

        if not from_pci:
            p.confirmation = confirmation
            p.source_address = None
        elif source_addr:
            p.source_address = source_addr
            p.confirmation = None
    except Exception as e:
        p = InvalidPacket(payload=data, exception=e)

    return p, consumed
