#!/usr/bin/env python
# cbus/protocol/application/enable.py - Enable Control Application
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

from cbus.common import *
import warnings

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

        assert packet != None, 'packet must not be none.'

        if self.packet.application == None:
            # no application set on the packet, set it.
            self.packet.application = APP_ENABLE
        elif self.packet.application != APP_ENABLE:
            raise ValueError, 'packet has a different application set already. cannot have multiple application SAL in the same packet.'

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
                    "Got less than 3 bytes of stray SAL for enable application (malformed packet)",
                    UserWarning)
                break

            command_code = ord(data[0])

            data = data[1:]

            if (command_code & 0x80) == 0x80:
                warnings.warn(
                    'Got unknown enable command %r, stopping processing prematurely'
                    % command_code, UserWarning)
                break

            if (command_code & 0x07) != 2:
                warnings.warn(
                    'Got invalid length for enable command %r, must be 2 (Enable s9.4.1)'
                    % command_code, UserWarning)
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

        print "data == %r" % data
        variable = ord(data[0])
        value = ord(data[1])

        data = data[2:]

        return cls(packet, variable, value), data

    def encode(self):
        if not (0 <= self.variable <= 255):
            raise ValueError, 'Network variable number (variable) must be in range 0 - 255 (got %r).' % self.variable

        if not (0 <= self.value <= 255):
            raise ValueError, 'Network variable value (value) must be in range 0 - 255 (got %r).' % self.value

        return super(EnableSetNetworkVariableSAL, self).encode() + [
            ENABLE_SET_NETWORK_VARIABLE, self.variable, self.value
        ]


class EnableApplication(object):
    """
	This class is called in the cbus.protocol.applications.APPLICATIONS dict in
	order to describe how to decode enable broadcast application events
	recieved from the network.
	
	Do not call this class directly.
	"""

    @classmethod
    def decode_sal(cls, data, packet):
        """
		Decodes a enable broadcast application packet and returns it's
		SAL(s).
		"""
        return EnableSAL.decode(data, packet)
