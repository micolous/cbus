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

from cbus.common import *
import warnings

__all__ = [
    'TemperatureApplication',
    'TemperatureSAL',
    'TemperatureBroadcastSAL',
]


class TemperatureSAL(object):
    """
	Base type for temperature broadcast application SALs.
	"""

    def __init__(self, packet=None, group_address=None):
        """
		This should not be called directly by your code!
		
		Use one of the subclasses of cbus.protocol.temperature.TemperatureSAL instead.
		"""
        self.packet = packet
        self.group_address = group_address

        assert packet != None, 'packet must not be none.'

        if self.packet.application == None:
            # no application set on the packet, set it.
            self.packet.application = APP_TEMPERATURE
        elif self.packet.application != APP_TEMPERATURE:
            raise ValueError, 'packet has a different application set already. cannot have multiple application SAL in the same packet.'

    @classmethod
    def decode(cls, data, packet):
        """
		Decodes a temperature broadcast application packet and returns it's SAL(s).
		
		:param data: SAL data to be parsed.
		:type data: str
		
		:param packet: The packet that this data is associated with.
		:type packet: cbus.protocol.base_packet.BasePacket
		
		:returns: The SAL messages contained within the given data.
		:rtype: list of cbus.protocol.application.temperature.TemperatureSAL
		
		"""
        output = []

        while data:
            # parse the data

            if len(data) < 3:
                # not enough data to go on.
                warnings.warn(
                    "Got less than 3 bytes of stray SAL for temperature application (malformed packet)",
                    UserWarning)
                break

            command_code = ord(data[0])
            group_address = ord(data[1])

            data = data[2:]

            #if command_code not in SAL_HANDLERS:
            if (command_code & 0x80) == 0x80:
                warnings.warn(
                    'Got unknown temperature command %r, stopping processing prematurely'
                    % command_code, UserWarning)
                break

            if (command_code & 0x07) != 2:
                warnings.warn(
                    'Got invalid length for temperature command %r, must be 2 (Temperature s9.4.1)'
                    % command_code, UserWarning)
                break

            sal, data = TemperatureBroadcastSAL.decode(data, packet,
                                                       command_code,
                                                       group_address)

            if sal:
                output.append(sal)
        return output

    def encode(self):
        """
		Encodes the SAL into a format for sending over the C-Bus network.
		"""
        if not validate_ga(self.group_address):
            raise ValueError, 'group_addr out of range (%d - %d), got %r' % (
                MIN_GROUP_ADDR, MAX_GROUP_ADDR, self.group_address)

        return []


class TemperatureBroadcastSAL(TemperatureSAL):
    """
	Temperature broadcast event SAL.
	
	Informs the network of the current temperature being sensed at a location.
	
	"""

    def __init__(self, packet, group_address, temperature):
        """
		Creates a new SAL Temperature Broadcast message.
		
		:param packet: The packet that this SAL is to be included in.
		:type packet: cbus.protocol.base_packet.BasePacket
		
		:param group_address: The group address that is reporting the temperature.
		:type group_address: int
		
		:param temperature: The temperature, in degrees celcius, between 0.0 and 63.75.
		:type temperature: float
		
		"""
        super(TemperatureBroadcastSAL, self).__init__(packet, group_address)

        self.temperature = temperature

    @classmethod
    def decode(cls, data, packet, command_code, group_address):
        """
		Do not call this method directly -- use TemperatureSAL.decode
		"""
        temperature = ord(data[0]) / 4.0
        data = data[1:]

        return cls(packet, group_address, temperature), data

    def encode(self):
        if not (0.0 <= self.temperature <= 63.75):
            raise ValueError, 'Temperature is out of bounds.  Must be between 0.0 and 63.75 celcius (got %r).' % self.temperature

        return super(TemperatureBroadcastSAL, self).encode() + [
            TEMPERATURE_BROADCAST, self.group_address,
            int(self.temperature * 4)
        ]


class TemperatureApplication(object):
    """
	This class is called in the cbus.protocol.applications.APPLICATIONS dict in
	order to describe how to decode temperature broadcast application events
	recieved from the network.
	
	Do not call this class directly.
	"""

    @classmethod
    def decode_sal(cls, data, packet):
        """
		Decodes a temperature broadcast application packet and returns it's
		SAL(s).
		"""
        return TemperatureSAL.decode(data, packet)
