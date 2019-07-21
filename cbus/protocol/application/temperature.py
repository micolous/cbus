#!/usr/bin/env python
# cbus/protocol/application/temperature.py - Temperature Broadcast Application
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

from __future__ import absolute_import
from __future__ import annotations

import abc
from typing import Optional, Sequence, Set, Tuple, Union

from six import byte2int, indexbytes, int2byte
import warnings

from cbus.common import Application, check_ga, TEMPERATURE_BROADCAST
from cbus.protocol.application.sal import BaseApplication, SAL

__all__ = [
    'TemperatureApplication',
    'TemperatureSAL',
    'TemperatureBroadcastSAL',
]


class TemperatureSAL(SAL, abc.ABC):
    """
    Base type for temperature broadcast application SALs.
    """

    def __init__(self, group_address: int):
        """
        This should not be called directly by your code!

        Use one of the subclasses of cbus.protocol.temperature.TemperatureSAL
        instead.
        """
        self.group_address = group_address

    @property
    def application(self) -> Union[int, Application]:
        return Application.TEMPERATURE

    @staticmethod
    def decode_sals(data: bytes) -> Sequence[TemperatureSAL]:
        """
        Decodes a temperature broadcast application packet and returns its
        SAL(s).

        :param data: SAL data to be parsed.

        :returns: The SAL messages contained within the given data.
        :rtype: list of cbus.protocol.application.temperature.TemperatureSAL

        """
        output = []

        while data:
            # parse the data

            if len(data) < 3:
                # not enough data to go on.
                warnings.warn(
                    'Got less than 3 bytes of stray SAL for temperature '
                    'application (malformed packet)', UserWarning)
                break

            command_code = byte2int(data)
            group_address = indexbytes(data, 1)

            data = data[2:]

            if (command_code & 0x80) == 0x80:
                warnings.warn(
                    'Got unknown temperature command {}, stopping processing '
                    'prematurely'.format(command_code), UserWarning)
                break

            if (command_code & 0x07) != 2:
                warnings.warn(
                    'Got invalid length for temperature command {}, must be 2 '
                    '(Temperature s9.4.1)'.format(command_code), UserWarning)
                break

            sal, data = TemperatureBroadcastSAL.decode(
                data, group_address)

            if sal:
                output.append(sal)
        return output

    def encode(self) -> bytes:
        """
        Encodes the SAL into a format for sending over the C-Bus network.
        """
        check_ga(self.group_address)
        return bytes()


class TemperatureBroadcastSAL(TemperatureSAL):
    """
    Temperature broadcast event SAL.

    Informs the network of the current temperature being sensed at a location.

    """

    def __init__(self, group_address: int, temperature: float):
        """
        Creates a new SAL Temperature Broadcast message.
        :param group_address: The group address that is reporting the
                              temperature.
        :type group_address: int

        :param temperature: The temperature, in degrees celsius, between 0.0
                            and 63.75.
        :type temperature: float

        """
        super(TemperatureBroadcastSAL, self).__init__(group_address)
        self.temperature = temperature

    @classmethod
    def decode(cls, data: bytes,
               group_address: int) -> Tuple[TemperatureSAL, bytes]:
        """
        Do not call this method directly -- use TemperatureSAL.decode
        """
        temperature = byte2int(data) / 4.0
        data = data[1:]

        return cls(group_address, temperature), data

    def encode(self) -> bytes:
        if not (0.0 <= self.temperature <= 63.75):
            raise ValueError(
                'Temperature is out of bounds. Must be between 0.0 and 63.75 '
                'celsius (got {}).'.format(self.temperature))

        return super().encode() + bytes([
            TEMPERATURE_BROADCAST, self.group_address,
            int(self.temperature * 4)
        ])


class TemperatureApplication(BaseApplication):
    """
    This class is called in the cbus.protocol.applications.APPLICATIONS dict in
    order to describe how to decode temperature broadcast application events
    recieved from the network.

    Do not call this class directly.
    """

    @staticmethod
    def supported_applications() -> Set[Application]:
        return {Application.TEMPERATURE}

    @staticmethod
    def decode_sals(data: bytes) -> Sequence[TemperatureSAL]:
        """
        Decodes a temperature broadcast application packet and returns it's
        SAL(s).
        """
        return TemperatureSAL.decode_sals(data)
