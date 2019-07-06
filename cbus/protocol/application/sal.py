#!/usr/bin/env python3
# cbus/protocol/application/sal.py - SAL interface
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
from typing import FrozenSet, List, Union

from cbus.common import Application

__all__ = ['SAL', 'BaseApplication']


class SAL(abc.ABC):
    """
    Describes an decoder/encoder

    """
    @abc.abstractmethod
    def encode(self) -> bytes:
        return bytes()

    @property
    @abc.abstractmethod
    def application(self) -> Union[int, Application]:
        raise NotImplementedError('application')


class BaseApplication(abc.ABC):
    """
    Describes an decoder for all commands sent to an application.
    """

    @staticmethod
    @abc.abstractmethod
    def supported_applications() -> FrozenSet[Union[int, Application]]:
        """
        Gets a list of supported Application IDs for the application.

        All application IDs must be in the range 0x00 - 0xff.
        """
        raise NotImplementedError('supported_applications')

    @staticmethod
    @abc.abstractmethod
    def decode_sals(data: bytes) -> List[SAL]:
        """
        Decodes a SAL message

        """
        raise NotImplementedError('decode_sals')
