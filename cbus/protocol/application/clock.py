#!/usr/bin/env python
# cbus/protocol/application/clock.py - Clock and Timekeeping Application
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

import abc
from datetime import date, time
from six import byte2int, indexbytes, int2byte
from struct import unpack, pack
from typing import List, FrozenSet, Union, Set
import warnings

from cbus.common import Application, ClockAttribute, ClockCommand
from cbus.protocol.application.sal import BaseApplication, SAL

__all__ = [
    'ClockApplication',
    'ClockSAL',
    'ClockUpdateSAL',
    'ClockRequestSAL',
]

_SUPPORTED_APPLICATIONS = frozenset({int(Application.CLOCK)})


class ClockSAL(SAL, abc.ABC):
    """
    Base type for clock and timekeeping application SALs.
    """

    @property
    def application(self) -> Application:
        return Application.CLOCK

    @staticmethod
    def decode_sals(data: bytes) -> List[ClockSAL]:
        """
        Decodes a clock broadcast application packet and returns it's SAL(s).

        :param data: SAL data to be parsed.
        :returns: The SAL messages contained within the given data.
        :rtype: list of cbus.protocol.application.clock.ClockSAL

        """
        output = []

        while data:
            # parse the data
            command_code = data[0]
            data = data[1:]

            if (command_code & 0x80) == 0x80:
                warnings.warn(
                    'Got unknown clock command {:x}; long form is not '
                    'used.'.format(command_code), UserWarning)
                break

            if (command_code & 0xE0) != 0:
                warnings.warn(
                    'Got unknown clock command {:x}; don\'t know how to '
                    'process the other bits.'.format(command_code),
                    UserWarning)
                break

            if (command_code & 0xf8) == ClockCommand.UPDATE_NETWORK_VARIABLE:
                sal, data = ClockUpdateSAL.decode(data, command_code)
            elif command_code == ClockCommand.REQUEST_REFRESH:
                sal, data = ClockRequestSAL.decode(data, command_code)
            else:
                # unknown
                warnings.warn(
                    'Got unknown clock command {:x}; last stage '
                    'dropout'.format(command_code), UserWarning)
                break

            if sal:
                output.append(sal)
        return output


class ClockUpdateSAL(ClockSAL):
    """
    Clock update event SAL.

    Informs the network of the current time.

    """

    @property
    def is_date(self):
        return isinstance(self.val, date)

    @property
    def is_time(self):
        return isinstance(self.val, time)

    def __init__(self, val: Union[date, time]):
        """
        Creates a new SAL Clock update message.

        :param variable: The variable being updated.
        :type variable: int

        :param val: The value of that variable. Dates are represented in
                    native date format, and times are represented in native
                    time format.
        :type val: datetime.date or datetime.time

        """
        super(ClockUpdateSAL, self).__init__()
        self.val = val

    @classmethod
    def decode(cls, data, command_code):
        """
        Do not call this method directly -- use ClockSAL.decode
        """

        variable = data[0]
        data_length = command_code & 0x07
        val = data[1:data_length]
        data = data[data_length:]

        if variable == ClockAttribute.DATE:
            # date (23.5.1.2)
            # length must be 0x06
            if data_length != 0x06:
                warnings.warn(
                    'Date variable being sent with length != 5 '
                    '(got {} instead)'.format(data_length), UserWarning)
                return None, data

            # now decode the date
            year, month, day, dow = unpack('>HBBB', val)
            # note: dow / day of week is ignored

            return cls(date(year, month, day)), data

        elif variable == ClockAttribute.TIME:
            # time (23.5.1.1)
            # length must be 0x05
            if data_length != 0x05:
                warnings.warn(
                    'Time variable being sent with length != 4 '
                    '(got {} instead)'.format(data_length), UserWarning)
                return None, data

            # now decode the time
            hour, minute, second, dst = unpack('>BBBB', val)
            # note: dst / daylight savings flag is ignored

            return cls(time(hour, minute, second)), data
        else:
            warnings.warn(
                'Tried to decode unknown clock update variable '
                '{:x}'.format(variable), UserWarning)
            # attempt to skip the bad data and recover
            return None, data[data_length:]

    def encode(self):
        if isinstance(self.val, time):
            # time
            # TODO: implement DST flag
            val = pack(
                '>BBBB', self.val.hour, self.val.minute, self.val.second, 255)
            attr = ClockAttribute.TIME
        elif isinstance(self.val, date):
            # date
            val = pack(
                '>HBBB', self.val.year, self.val.month, self.val.day,
                self.val.weekday())
            attr = ClockAttribute.DATE
        else:
            # unknown
            raise ValueError("Don't know how to pack clock variable %r" %
                             self.val)

        return super(ClockUpdateSAL, self).encode() + bytes([
            0x08 | (len(val) + 1),
            attr]) + val


class ClockRequestSAL(ClockSAL):
    """
    Clock request event SAL.

    Requests network time.

    """

    def __init__(self):
        """
        Creates a new SAL Clock request message.
        """
        super(ClockRequestSAL, self).__init__()

    @classmethod
    def decode(cls, data, command_code):
        """
        Do not call this method directly -- use ClockSAL.decode
        """

        argument = byte2int(data)
        data = data[1:]

        if argument != 0x03:
            warnings.warn(
                'Request refresh argument != 3 (got %d instead)' % argument,
                UserWarning)
            return None, data

        return cls(), data

    def encode(self):
        return super().encode() + bytes([
            ClockCommand.REQUEST_REFRESH, 0x03])


class ClockApplication(BaseApplication):
    """
    This class is called in the cbus.protocol.applications.APPLICATIONS dict in
    order to describe how to decode clock and timekeeping application events
    received from the network.

    Do not call this class directly.
    """

    @staticmethod
    def supported_applications() -> Set[Application]:
        return {Application.CLOCK}

    @staticmethod
    def decode_sals(data: bytes) -> List[SAL]:
        """
        Decodes a clock and timekeeping application packet and returns its
        SAL(s).
        """
        return ClockSAL.decode_sals(data)
