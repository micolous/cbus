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

from six import byte2int, indexbytes, int2byte
import warnings

from cbus.common import APP_ENABLE, ENABLE_SET_NETWORK_VARIABLE

__all__ = [
    'EnableApplication',
    'EnableSAL',
    'EnableSetNetworkVariableSAL',
]


class EnableSAL(object):
    """
    Base type for enable control application SALs.
    """

    def __init__(self, packet=None):
        """
        This should not be called directly by your code!

        Use one of the subclasses of cbus.protocol.enable.EnableSAL instead.
        """
        self.packet = packet

        if packet is None:
            raise ValueError('packet must not be None')

        if self.packet.application is None:
            # no application set on the packet, set it.
            self.packet.application = APP_ENABLE
        elif self.packet.application != APP_ENABLE:
            raise ValueError(
                'packet has a different application set already. Cannot have '
                'multiple application SAL in the same packet.')

    @classmethod
    def decode(cls, data, packet):
        """
        Decodes a enable control application packet and returns it's SAL(s).

        :param data: SAL data to be parsed.
        :type data: str

        :param packet: The packet that this data is associated with.
        :type packet: cbus.protocol.base_packet.BasePacket

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

            sal, data = EnableSetNetworkVariableSAL.decode(
                data, packet, command_code)

            if sal:
                output.append(sal)
        return output

    def encode(self):
        """
        Encodes the SAL into a format for sending over the C-Bus network.
        """
        return []


class EnableSetNetworkVariableSAL(EnableSAL):
    """
    Enable control Set Network Variable SAL.

    Sets a network variable.

    """

    def __init__(self, packet, variable, value):
        """
        Creates a new SAL Enable Control Set Network Variable

        :param packet: The packet that this SAL is to be included in.
        :type packet: cbus.protocol.base_packet.BasePacket

        :param variable: The variable ID being changed
        :type variable: int

        :param value: The value of the network variable
        :type value: int

        """
        super(EnableSetNetworkVariableSAL, self).__init__(packet)

        self.variable = variable
        self.value = value

    @classmethod
    def decode(cls, data, packet, command_code):
        """
        Do not call this method directly -- use EnableSAL.decode
        """

        # print "data == %r" % data
        variable = byte2int(data)
        value = indexbytes(data, 1)

        data = data[2:]

        return cls(packet, variable, value), data

    def encode(self):
        if self.variable < 0 or self.variable > 0xff:
            raise ValueError('Network variable number (variable) must be in '
                             'range 0..255 (got {}).'.format(self.variable))

        if self.value < 0 or self.value > 0xff:
            raise ValueError('Network variable value (value) must be in '
                             'range 0..255 (got {}).'.format(self.value))

        return super(EnableSetNetworkVariableSAL, self).encode() + [
            ENABLE_SET_NETWORK_VARIABLE, self.variable, self.value
        ]


class EnableApplication(object):
    """
    This class is called in the cbus.protocol.applications.APPLICATIONS dict in
    order to describe how to decode enable broadcast application events
    received from the network.

    Do not call this class directly.
    """

    @classmethod
    def decode_sal(cls, data, packet):
        """
        Decodes a enable broadcast application packet and returns its SAL(s).
        """
        return EnableSAL.decode(data, packet)
