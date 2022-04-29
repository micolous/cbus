#!/usr/bin/env python
# cbus/protocol/application/lighting.py - Lighting Application
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
from __future__ import annotations

import abc
from typing import FrozenSet, List, Optional, Tuple, Union
import warnings

from cbus.protocol.application.sal import BaseApplication, SAL
from cbus.common import (
    Application, LightCommand, LIGHT_RAMP_COMMANDS,
    check_ga, duration_to_ramp_rate, ramp_rate_to_duration)

__all__ = [
    'LightingApplication',
    'LightingSAL',
    'LightingRampSAL',
    'LightingOnSAL',
    'LightingOffSAL',
    'LightingTerminateRampSAL',
]

# Put the main lighting application first in the set.
_SUPPORTED_APPLICATIONS = frozenset(
    {int(Application.LIGHTING)} |
    {int(x) for x in range(Application.LIGHTING_FIRST,
                           Application.LIGHTING_LAST + 1)
     if x != Application.LIGHTING})


class LightingSAL(SAL, abc.ABC):
    """
    Base type for lighting application SALs.
    """

    def __init__(self, group_address: int, application_address: Union[Application,int]):
        """
        This should not be called directly by your code!

        Use one of the subclasses of cbus.protocol.lighting.LightingSAL
        instead.
        """
        #TODO: modify to avoid redundancy
        if not application_address in _SUPPORTED_APPLICATIONS:
            raise ValueError('Expected light Application address, got {}'.format(application_address))
        check_ga(group_address)
        self.application_address = application_address
        self.group_address = group_address

    @property
    def application(self) -> Union[int, Application]:
        return self.application_address 

    @staticmethod
    def decode_sals(data: bytes, application: int | Application ) -> List[LightingSAL]:
        """
        Decodes a lighting application packet and returns it's SAL(s).

        :param data: SAL data to be parsed.

        :returns: The SAL messages contained within the given data.
        :rtype: list of cbus.protocol.application.lighting.LightingSAL

        """
        output = []

        while data:
            # parse the data

            if len(data) < 2:
                # not enough data to go on.
                warnings.warn(
                    'Got 1 byte of stray SAL for lighting application '
                    '(malformed packet): {}'.format(data), UserWarning)
                break

            command_code = data[0]
            group_address = data[1]
            data = data[2:]

            if command_code not in _SAL_HANDLERS:
                warnings.warn(
                    'Got unknown lighting command {}, stopping processing '
                    'prematurely'.format(command_code), UserWarning)
                break

            sal, data = _SAL_HANDLERS[command_code].decode(
                data, command_code, group_address,application)

            if sal:
                output.append(sal)
        return output

    @abc.abstractmethod
    def encode(self) -> bytes:
        """
        Encodes the SAL into a format for sending over the C-Bus network.
        """
        check_ga(self.group_address)
        return bytes()

    @staticmethod
    @abc.abstractmethod
    def decode(data: bytes, command_code: int,
               group_address: int) -> Tuple[Optional[LightingSAL], bytes]:
        raise NotImplementedError('decode')


class LightingRampSAL(LightingSAL):
    """
    Lighting Ramp (fade) event SAL

    Instructs the given group address to fade to a lighting level (brightness)
    over a given duration.

    """

    def __init__(self, group_address: int,application_address: Union[int,Application] , duration: int, level: int ):
        """
        Creates a new SAL Lighting Ramp message.

        :param group_address: The group address to ramp.
        :type group_address: int

        :param duration: The duration to ramp over, in seconds.
        :type duration: int

        :param level: The level to ramp to, with 0 indicating off, and 255
                      indicating full brightness.
        :type level: int
        """
        super().__init__(group_address,application_address )

        self.duration = duration
        self.level = level

    @staticmethod
    def decode(data: bytes, command_code: int,
               group_address: int, application_address: int | Application) -> Tuple[Optional[LightingSAL], bytes]:
        """
        Do not call this method directly -- use LightingSAL.decode
        """
        duration = ramp_rate_to_duration(command_code)

        if not data:
            warnings.warn(
                'Couldn\'t get level for LightingRampSAL, no more data.',
                UserWarning)
            return None, data

        level = data[0]
        data = data[1:]

        return LightingRampSAL(
            group_address=group_address, application_address=application_address,duration=duration, level=level), data

    def encode(self) -> bytes:
        if self.level < 0 or self.level > 255:
            raise ValueError(
                f'Ramp level is out of bounds 0..255 (got {self.level})')

        return super().encode() + bytes([
            duration_to_ramp_rate(self.duration), self.group_address,
            self.level
        ])

    def __repr__(self):
        return (
            '<LightingRampSAL object: group_address={}, duration={}, '
            'level={}>'.format(self.group_address, self.duration, self.level))


class LightingOnSAL(LightingSAL):
    """
    Lighting on event SAL

    Instructs a given group address to turn it's load on.
    """

    @staticmethod
    def decode(data: bytes, command_code: int,
               group_address: int, application_address: int | Application) -> Tuple[LightingOnSAL, bytes]:
        """
        Do not call this method directly -- use LightingSAL.decode
        """
        return LightingOnSAL(group_address,application_address), data

    def encode(self):
        return super().encode() + bytes([LightCommand.ON, self.group_address])

    def __repr__(self):
        return '<LightingOnSAL object: group_address=%r>' % self.group_address


class LightingOffSAL(LightingSAL):
    """
    Lighting off event SAL

    Instructs a given group address to turn it's load off.
    """

    @staticmethod
    def decode(data: bytes, command_code: int,
               group_address: int, application_address: int | Application) -> Tuple[LightingOffSAL, bytes]:
        """
        Do not call this method directly -- use LightingSAL.decode
        """
        return LightingOffSAL(group_address,application_address), data

    def encode(self):
        return super().encode() + bytes([LightCommand.OFF, self.group_address])

    def __repr__(self):
        return '<LightingOffSAL object: group_address=%r>' % self.group_address


class LightingTerminateRampSAL(LightingSAL):
    """
    Lighting terminate ramp event SAL

    Instructs the given group address to discontinue any ramp operations in
    progress, and use the brightness that they are currently at.
    """

    @staticmethod
    def decode(data: bytes, command_code: int,
               group_address: int, application_address: int | Application)  -> Tuple[LightingTerminateRampSAL, bytes]:
        """
        Do not call this method directly -- use LightingSAL.decode
        """
        return LightingTerminateRampSAL(group_address,application_address), data

    def encode(self):
        return super().encode() + bytes([
            LightCommand.TERMINATE_RAMP, self.group_address])

    def __repr__(self):
        return ('<LightingTerminateRampSAL object: '
                'group_address={}>'.format(self.group_address))


# register SAL handlers (used by LightingSAL to map commands)
_SAL_HANDLERS = {
    LightCommand.ON: LightingOnSAL,
    LightCommand.OFF: LightingOffSAL,
    LightCommand.TERMINATE_RAMP: LightingTerminateRampSAL,
}

for x in LIGHT_RAMP_COMMANDS:
    if x in _SAL_HANDLERS:
        raise ValueError(
            'LightingRampSAL attempted registration of existing command code!')
    _SAL_HANDLERS[x] = LightingRampSAL


class LightingApplication(BaseApplication):
    """
    This class is called in the cbus.protocol.applications.APPLICATIONS dict in
    order to describe how to decode lighting application events recieved from
    the network.

    Do not call this class directly.
    """

    @staticmethod
    def decode_sals(data: bytes, application: int | Application ) -> List[SAL]:
        return LightingSAL.decode_sals(data,application)

    @staticmethod
    def supported_applications() -> FrozenSet[int]:
        return _SUPPORTED_APPLICATIONS
