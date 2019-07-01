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
from cbus.protocol.application.clock import ClockApplication
from cbus.protocol.application.enable import EnableApplication
from cbus.protocol.application.lighting import LightingApplication
from cbus.protocol.application.temperature import TemperatureApplication
from cbus.common import APP_CLOCK, APP_ENABLE, APP_LIGHTING, APP_TEMPERATURE

APPLICATIONS = {
    APP_CLOCK: ClockApplication,
    APP_ENABLE: EnableApplication,
    APP_LIGHTING: LightingApplication,
    APP_TEMPERATURE: TemperatureApplication,
}
