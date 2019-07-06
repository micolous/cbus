#!/usr/bin/env python
# cbus/protocol/application/__init__.py - Applications in CBus
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

from typing import Type

from cbus.protocol.application.sal import BaseApplication
from cbus.protocol.application.status_request import StatusRequestApplication
from cbus.protocol.application.clock import ClockApplication
from cbus.protocol.application.enable import EnableApplication
from cbus.protocol.application.lighting import LightingApplication
from cbus.protocol.application.temperature import TemperatureApplication

__all__ = ['get_application']


_APPLICATIONS = frozenset([
    StatusRequestApplication,
    ClockApplication,
    EnableApplication,
    LightingApplication,
    TemperatureApplication,
])
_APPLICATIONS_DICT = {}


def get_application(app_id: int) -> Type[BaseApplication]:
    return _APPLICATIONS_DICT[app_id]


def _register_application(app: Type[BaseApplication]) -> None:
    """
    Adds the application the registry.

    :param app: Reference to BaseApplication type.
    """

    app_ids = app.supported_applications()
    if not all((0 <= i <= 0xff for i in app_ids)):
        raise ValueError('Application IDs must be in range 0x00-0xff')

    for i in app_ids:
        o = _APPLICATIONS_DICT.setdefault(i, app)
        if o is not None and o is not app:
            raise ValueError(
                f'Attempted to register application {i:x} for {app:r}, '
                f'which is already registered by {o:r}')


for app in _APPLICATIONS:
    _register_application(app)
