#!/usr/bin/env python
# cbus/common.py - Constants and common functions used in the CBUS protocol.
# Copyright 2012-2013 Michael Farrell <micolous+git@gmail.com>
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
"""
cbus.common defines various common helper utilities used by the library, and
constants required to communicate with the C-Bus network.

The majority of the functionality shouldn't be needed by your own application,
however it is used internally within the protocol encoders and decoders.
"""

from __future__ import absolute_import
from enum import IntEnum
import logging

HEX_CHARS = b'0123456789ABCDEF'

# Serial Interface User Guide, s4.2.1 (Structure of Commands)
# "Each command is terminated with a carriage return (ASCII character 13,
# hex $0D)"
END_COMMAND = b'\x0d'

# Serial Interface User Guide, s4.3.2 (Structure of Replies)
# "Each reply (except Confirmation) is terminated with a carriage return,
# line feed pair (ASCII character 13, hex $0D; followed by ASCII character
# 10, hex $0A)"
END_RESPONSE = b'\x0d\x0a'

MIN_MESSAGE_SIZE = 2
MAX_BUFFER_SIZE = 256


class DestinationAddressType(IntEnum):
    """
    Destination Address Type (DAT).

    Ref: Serial Interface Guide, s3.4. Other values reserved.
    """
    UNSET = 0x00
    POINT_TO_POINT_TO_MULTIPOINT = 0x03
    POINT_TO_MULTIPOINT = 0x05
    POINT_TO_POINT = 0x06


class PriorityClass(IntEnum):
    CLASS_4 = 0x00  # lowest
    CLASS_3 = 0x01  # medium low
    CLASS_2 = 0x02  # medium high
    CLASS_1 = 0x03  # highest


# undocumented command type issued for status inquiries by toolkit?
# POINT_TO_46 = '\\46'

# Applications
class Application(IntEnum):
    TEMPERATURE = 0x19
    LIGHTING_FIRST = LIGHTING_30 = 0x30
    LIGHTING_31 = 0x31
    LIGHTING_32 = 0x32
    LIGHTING_33 = 0x33
    LIGHTING_34 = 0x34
    LIGHTING_35 = 0x35
    LIGHTING_36 = 0x36
    LIGHTING_37 = 0x37
    LIGHTING = LIGHTING_38 = 0x38
    LIGHTING_39 = 0x39
    LIGHTING_3a = 0x3a
    LIGHTING_3b = 0x3b
    LIGHTING_3c = 0x3c
    LIGHTING_3d = 0x3d
    LIGHTING_3e = 0x3e
    LIGHTING_3f = 0x3f
    LIGHTING_40 = 0x40
    LIGHTING_41 = 0x41
    LIGHTING_42 = 0x42
    LIGHTING_43 = 0x43
    LIGHTING_44 = 0x44
    LIGHTING_45 = 0x45
    LIGHTING_46 = 0x46
    LIGHTING_47 = 0x47
    LIGHTING_48 = 0x48
    LIGHTING_49 = 0x49
    LIGHTING_4a = 0x4a
    LIGHTING_4b = 0x4b
    LIGHTING_4c = 0x4c
    LIGHTING_4d = 0x4d
    LIGHTING_4e = 0x4e
    LIGHTING_4f = 0x4f
    LIGHTING_50 = 0x50
    LIGHTING_51 = 0x51
    LIGHTING_52 = 0x52
    LIGHTING_53 = 0x53
    LIGHTING_54 = 0x54
    LIGHTING_55 = 0x55
    LIGHTING_56 = 0x56
    LIGHTING_57 = 0x57
    LIGHTING_58 = 0x58
    LIGHTING_59 = 0x59
    LIGHTING_5a = 0x5a
    LIGHTING_5b = 0x5b
    LIGHTING_5c = 0x5c
    LIGHTING_5d = 0x5d
    LIGHTING_5e = 0x5e
    LIGHTING_LAST = LIGHTING_5f = 0x5f
    HVACACTUATOR_73 = 0x73
    HVACACTUATOR_74 = 0x74
    HVAC = 0xCA
    CLOCK = 0xDF
    TRIGGER = 0xCA
    ENABLE = 0xCB
    MASTER_APPLICATION = STATUS_REQUEST = 0xff

    def isLighting(val):
        if isinstance(val,Application):
          val = int(val)
        if isinstance(val,int):
          return int(Application.LIGHTING_FIRST)<=val<=int(Application.LIGHTING_LAST)
        return False

    def isHvacActuator(val):
        if isinstance(val,Application):
          val = int(val)
        if isinstance(val,int):
          return int(Application.HVACACTUATOR_73)==val or int(Application.HVACACTUATOR_74)==val
        return False


class CAL(IntEnum):
    RESET = 0x08
    RECALL = 0x1a
    IDENTIFY = 0x21
    GET_STATUS = 0x2a
    ACKNOWLEDGE = 0x32

    # These are bit-masks
    REPLY = 0x80
    STANDARD_STATUS = 0xc0
    EXTENDED_STATUS = 0xe0


class ExtendedCALType(IntEnum):
    BINARY = 0x00
    LEVEL = 0x07


class GroupState(IntEnum):
    MISSING = 0x00
    ON = 0x01
    OFF = 0x02
    ERROR = 0x03


class IdentifyAttribute(IntEnum):
    """
    IDENTIFY attributes.

    See Serial Interface Guide, s7.2.
    """
    MANUFACTURER = 0x00
    TYPE = 0x01
    FIRMWARE_VER = 0x02
    SUMMARY = 0x03
    EXTENDED = 0x04
    NET_TERM_LVL = 0x05
    TERM_LVL = 0x06
    NET_VOLTAGE = 0x07
    GAV_CURRENT = 0x08
    GAV_STORED = 0x09
    GAV_PHY_ADDR = 0x0A
    LOGIC_ASSIGN = 0x0B
    DELAYS = 0x0C
    MIN_LVL = 0x0D
    MAX_LVL = 0x0E
    CUR_LVL = 0x0F
    OUT_SUMMARY = 0x10
    DSI_STATUS = 0x11


# Routing buffer
ROUTING_NONE = 0x00


# Enable control application commands.
class EnableCommand(IntEnum):
    SET_NETWORK_VARIABLE = 0x02


# temperature broadcast commands.
TEMPERATURE_BROADCAST = 0x02


# lighting application commands.
class LightCommand(IntEnum):
    # light on
    # \0538007964 (GA 100)
    ON = 0x79

    # light off
    # \0538000164 (GA 100)
    OFF = 0x01

    RAMP_INSTANT = RAMP_FASTEST = 0x02
    RAMP_00_04 = 0x0a
    RAMP_00_08 = 0x12
    RAMP_00_12 = 0x1a
    RAMP_00_20 = 0x22
    RAMP_00_30 = 0x2a
    RAMP_00_40 = 0x32
    RAMP_01_00 = 0x3a
    RAMP_01_30 = 0x42
    RAMP_02_00 = 0x4a
    RAMP_03_00 = 0x52
    RAMP_05_00 = 0x5a
    RAMP_07_00 = 0x62
    RAMP_10_00 = 0x6a
    RAMP_15_00 = 0x72
    RAMP_17_00 = RAMP_SLOWEST = 0x7a

    # set to level
    # \053800rr64FF (GA 100, to level 100%/0xff)
    TERMINATE_RAMP = 0x09

    # note that 0xA0 - 0xA2 are invalid (minimum label length = 3)
    # Lighting Application s2.6.5 p11
    LIGHT_LABEL = 0xA0


_LIGHT_RAMP_RATES = {
    LightCommand.RAMP_INSTANT: 0,
    LightCommand.RAMP_00_04: 4,
    LightCommand.RAMP_00_08: 8,
    LightCommand.RAMP_00_12: 12,
    LightCommand.RAMP_00_20: 20,
    LightCommand.RAMP_00_30: 30,
    LightCommand.RAMP_00_40: 40,
    LightCommand.RAMP_01_00: 60,
    LightCommand.RAMP_01_30: 90,
    LightCommand.RAMP_02_00: 120,
    LightCommand.RAMP_03_00: 180,
    LightCommand.RAMP_05_00: 300,
    LightCommand.RAMP_07_00: 420,
    LightCommand.RAMP_10_00: 600,
    LightCommand.RAMP_15_00: 900,
    LightCommand.RAMP_17_00: 1020,
}

_LIGHT_RAMP_DURATION_TO_RATE = [
    (d, c) for c, d in sorted(_LIGHT_RAMP_RATES.items(), key=lambda x: x[1])]
LIGHT_RAMP_COMMANDS = set(_LIGHT_RAMP_RATES.keys())


# Fastest ramp rate
LIGHT_RAMP_FASTEST_DURATION = _LIGHT_RAMP_DURATION_TO_RATE[0][0]
LIGHT_RAMP_SLOWEST_DURATION = _LIGHT_RAMP_DURATION_TO_RATE[-1][0]


class ClockAttribute(IntEnum):
    TIME = 0x01
    DATE = 0x02


class ClockCommand(IntEnum):
    UPDATE_NETWORK_VARIABLE = 0x08
    REQUEST_REFRESH = 0x11


RECALL = 0x1A
IDENTIFY = 0x21

# Lighting Application s2.4.3 s6-7
# TODO: finish entering the list
LANGUAGE_CODES = {
    # english and dialects
    0x01: 'en',
    0x02: 'en-AU',
    0x03: 'en-BZ',
    0x04: 'en-CA',
    # 0x05: English (Carribean)
    0x06: 'en-IE',
    0x07: 'en-JM',
    0x08: 'en-NZ',
    0x09: 'en-PH',
    0x0A: 'en-ZA',
    0x0B: 'en-TT',
    0x0C: 'en-GB',
    0x0D: 'en-US',
    0x0E: 'en-ZW',
    0x40: 'af',  # afrikaans
    0x41: 'eu',  # basque
    0x42: 'ca',  # catalan
    0x43: 'da',  # danish
    0x44: 'nl-BE',  # dutch (belgium)
    0x45: 'nl-NL',  # dutch (netherlands)
    0x46: 'fo',  # faroese
    0x47: 'fi',  # finnish
    0x48: 'fr-BE',  # french (belgium)
    0x49: 'fr-CA',  # french (canada)
    0x4A: 'fr',  # french
    0x4B: 'fr-LU',  # french (luxembourg)
    0x4C: 'fr-MC',  # french (monaco)
    0x4D: 'fr-CH',  # french (switzerland)
    0x4E: 'gl',  # galician
    0x4F: 'de-AT',  # german (austria)
    0x50: 'de',  # german
}
# these are valid confirmation codes used in acknowledge events.
CONFIRMATION_CODES = b'hijklmnopqrstuvwxyzg'

MIN_GROUP_ADDR = 0
MAX_GROUP_ADDR = 255

# bridge length
BRIDGE_LENGTHS = {0x09: 0, 0x12: 1, 0x1B: 2, 0x24: 3, 0x2D: 4, 0x36: 5}

logging.basicConfig(format='%(asctime)s %(message)s')


def duration_to_ramp_rate(seconds: int) -> LightCommand:
    """
    Converts a given duration into a ramp rate code.

    :param seconds: The number of seconds that the ramp is over.
    :type seconds: int

    :returns: The ramp rate code for the duration given.
    :rtype: int
    """
    for d, cmd in _LIGHT_RAMP_DURATION_TO_RATE:
        if seconds <= d:
            return cmd

    return LightCommand.RAMP_SLOWEST


def ramp_rate_to_duration(rate: int) -> int:
    """
    Converts a given ramp rate code into a duration in seconds.

    :param rate: The ramp rate code to convert.
    :type rate: int

    :returns: The number of seconds the ramp runs over.
    :rtype: int

    :raises KeyError: If the given ramp rate code is invalid.
    """

    return _LIGHT_RAMP_RATES[rate]


def cbus_checksum(i: bytes) -> int:
    """
    Calculates the checksum of a C-Bus command string.

    Fun fact: C-Bus toolkit and C-Gate do not use commands with checksums.

    :param i: The C-Bus data to calculate the checksum of. Must not be in
              base16 format.
    :type i: bytes

    :returns: The checksum value of the given input
    """
    c = 0
    for x in i:
        c += x

    c = ((c & 0xff) ^ 0xff) + 1

    return c & 0xff


def add_cbus_checksum(i: bytes) -> bytes:
    """
    Appends a C-Bus checksum to a given message.

    :param i: The C-Bus message to append a checksum to. Must not be in base16
              format.
    :type i: bytes

    :returns: The C-Bus message with the checksum appended to it.
    :rtype: bytes
    """
    c = cbus_checksum(i)
    return i + bytes([c])


def validate_cbus_checksum(i: bytes) -> bool:
    """
    Verifies a C-Bus checksum from a given message.

    :param i: The C-Bus message to verify the checksum of, in raw format.

    :returns: True if the checksum is correct, False otherwise.
    """
    packet_checksum = i[-1]
    actual_checksum = get_real_cbus_checksum(i)
    return packet_checksum == actual_checksum


def get_real_cbus_checksum(i: bytes) -> int:
    """
    Calculates the current C-Bus checksum for a given message which already has
    a checksum appended to it.

    :param i: The C-Bus message to generate an actual checksum for, in raw
              format.
    """
    d = i[:-1]
    return cbus_checksum(d)


def validate_ga(group_addr: int) -> bool:
    """
    Validates a given group address.

    :param group_addr: Input group address to validate.

    :returns: True if the given group address is valid, False otherwise.

    """
    return MIN_GROUP_ADDR <= group_addr <= MAX_GROUP_ADDR


def check_ga(group_addr: int) -> None:
    """
    Validates a given group address, throwing ValueError if not.

    :param group_addr: Input group address to validate.
    :raises ValueError: If group address is invalid

    """
    if not validate_ga(group_addr):
        raise ValueError(
            'Group Address out of range ({}..{}), got {}'.format(
                MIN_GROUP_ADDR, MAX_GROUP_ADDR, group_addr))


def check_aa_lighting(app_addr: int | Application) -> None:
     if not Application.isLighting(app_addr):
        raise ValueError(
            'Expected lighting application address, got {}'.format(app_addr))