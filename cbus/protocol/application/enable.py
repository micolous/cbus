#!/usr/bin/env python
# cbus/protocol/application/enable.py - Enable Control Application
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
from __future__ import annotations

from typing import Union, Set, List

from six import byte2int, indexbytes, int2byte
import warnings

from cbus.common import Application, EnableCommand
from cbus.protocol.application.sal import BaseApplication, SAL

__all__ = [
    'EnableApplication',
    'EnableSAL',
    'EnableSetNetworkVariableSAL',
]


class EnableSAL(SAL):
    """
    Base type for enable control application SALs.
    """

    @property
    def application(self) -> Application:
        return Application.ENABLE

    @staticmethod
    def decode_sals(data: bytes) -> List[EnableSAL]:
        """
        Decodes a enable control application packet and returns it's SAL(s).

        :param data: SAL data to be parsed.
        :type data: str

        :returns: The SAL messages contained within the given data.
        :rtype: list of cbus.protocol.application.enable.EnableSAL

        """
        output = []

        while data:
            # parse the data

            if len(data) < 3:
                # not enough data to go on.
                warnings.warn(
                    'Got less than 3 bytes of stray SAL for enable '
                    'application (malformed packet)', UserWarning)
                break

            command_code = byte2int(data)

            data = data[1:]

            if (command_code & 0x80) == 0x80:
                warnings.warn(
                    'Got unknown enable command {}, stopping processing '
                    'prematurely'.format(command_code), UserWarning)
                break

            if (command_code & 0x07) != 2:
                warnings.warn(
                    'Got invalid length for enable command {}, must be '
                    '2 (Enable s9.4.1)'.format(command_code), UserWarning)
                break

            sal, data = EnableSetNetworkVariableSAL.decode(data)

            if sal:
                output.append(sal)
        return output


class EnableSetNetworkVariableSAL(EnableSAL):
    """
    Enable control Set Network Variable SAL.

    Sets a network variable.

    """

    def __init__(self, variable, value):
        """
        Creates a new SAL Enable Control Set Network Variable

        :param variable: The variable ID being changed
        :type variable: int

        :param value: The value of the network variable
        :type value: int

        """
        super().__init__()

        self.variable = variable
        self.value = value

    @classmethod
    def decode(cls, data):
        """
        Do not call this method directly -- use EnableSAL.decode
        """

        # print "data == %r" % data
        variable = byte2int(data)
        value = indexbytes(data, 1)

        data = data[2:]

        return cls(variable, value), data

    def encode(self) -> bytes:
        variable = self.variable & 0xff
        value = self.value & 0xff

        return super().encode() + bytes([
            EnableCommand.SET_NETWORK_VARIABLE, variable, value
        ])


class EnableApplication(BaseApplication):
    """
    This class is called in the cbus.protocol.applications.APPLICATIONS dict in
    order to describe how to decode enable broadcast application events
    received from the network.

    Do not call this class directly.
    """

    @staticmethod
    def supported_applications() -> Set[Application]:
        return {Application.ENABLE}

    @classmethod
    def decode_sals(cls, data: bytes) -> List[EnableSAL]:
        """
        Decodes a enable broadcast application packet and returns its SAL(s).
        """
        return EnableSAL.decode_sals(data)
