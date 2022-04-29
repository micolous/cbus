#!/usr/bin/env python
# cbus/protocol/application/clock.py - Clock and Timekeeping Application
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
import warnings
from datetime import date, time, datetime
from struct import unpack, pack
from typing import Union, Set, Sequence, Tuple, Optional

from six import byte2int

from cbus.common import Application, ClockAttribute, ClockCommand
from cbus.protocol.application.sal import BaseApplication, SAL

__all__ = [
    'ClockApplication',
    'ClockSAL',
    'ClockUpdateSAL',
    'ClockRequestSAL',
    'clock_update_sal',
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
    def decode_sals(data: bytes,_=None) -> Sequence[ClockSAL]:
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
                sal, data = ClockRequestSAL.decode(data)
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

        Use ``clock_update_sal(val)`` instead of this constructor, as that
        method handles ``datetime.datetime`` objects (in addition to
        ``datetime.date`` and ``datetime.time``, always returns
        ``Sequence[ClockUpdateSAL]``.

        :param val: The value of that variable. Dates are represented in
                    native date format, and times are represented in native
                    time format.
        """
        super(ClockUpdateSAL, self).__init__()
        self.val = val

    @classmethod
    def decode(cls, data: bytes,
               command_code: int) -> Tuple[Optional[ClockSAL], bytes]:
        """
        Do not call this method directly -- use ClockSAL.decode
        """

        variable = data[0]
        data_length = command_code & 0x07  # len(variable name + value)
        val = data[1:data_length]
        data = data[data_length:]

        if variable == ClockAttribute.DATE:
            # date (23.5.1.2)
            # length must be 0x06
            if data_length != 0x06:
                warnings.warn(
                    f'Ignoring date variable with length {data_length} '
                    f'(expected 6)', UserWarning)
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
                    f'Ignoring date variable with length {data_length} '
                    f'(expected 5)', UserWarning)
                return None, data

            # now decode the time
            hour, minute, second, dst = unpack('>BBBB', val)
            # note: dst / daylight savings flag is ignored

            return cls(time(hour, minute, second)), data
        else:
            warnings.warn(
                f'Tried to decode unknown clock update variable {variable:x}',
                UserWarning)

            # attempt to skip the bad data and recover
            return None, data[data_length:]

    def encode(self) -> bytes:
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
            raise TypeError(f"Don't know how to pack clock variable {self.val}")

        return super().encode() + bytes([
            0x08 | (len(val) + 1),
            attr]) + val

    def __repr__(self):
        return f'{self.__class__.__name__}(val={self.val!r})'


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
    def decode(cls, data: bytes) -> Tuple[Optional[ClockSAL], bytes]:
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

    def encode(self) -> bytes:
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
    def decode_sals(data: bytes,_=None) -> Sequence[SAL]:
        """
        Decodes a clock and timekeeping application packet and returns its
        SAL(s).
        """
        return ClockSAL.decode_sals(data)


def clock_update_sal(
        val: Union[date, time, datetime]) -> Sequence[ClockUpdateSAL]:
    """Creates Clock Update SAL(s) based on Python datetime objects.

    :param val: The value to set in the ``ClockUpdateSAL``. If this is a
        ``datetime.datetime``, this will create multiple ``ClockUpdateSAL``
        objects. If this is a ``datetime.date`` or ``datetime.time``,
        this will only create only a single ``ClockUpdateSAL``.

    :returns: Sequence of ``ClockUpdateSAL``, regardless of input value type.
    :raises TypeError: On invalid input type.
    """
    if isinstance(val, datetime):
        return ClockUpdateSAL(val.date()), ClockUpdateSAL(val.time())
    elif isinstance(val, (date, time)):
        return ClockUpdateSAL(val),
    else:
        raise TypeError(
            f'val must be date, time, or datetime, instead got {type(val)!r}')
