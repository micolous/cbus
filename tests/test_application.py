#!/usr/bin/env python
# test_application.py - Internal application registration tests.
# Copyright 2019 Michael Farrell <micolous+git@gmail.com>
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

import unittest

from cbus.common import Application
from cbus.protocol.application import _register_application, get_application
from cbus.protocol.application.sal import BaseApplication


class InvalidLowAppIDApplication(BaseApplication):
    @staticmethod
    def supported_applications():
        return frozenset([-1])

    @staticmethod
    def decode_sals(data):
        return []


class InvalidHighAppIDApplication(BaseApplication):
    @staticmethod
    def supported_applications():
        return frozenset([0x100])

    @staticmethod
    def decode_sals(data):
        return []


class InvalidFakeLightingApplication(BaseApplication):
    @staticmethod
    def supported_applications():
        return frozenset([Application.LIGHTING])

    @staticmethod
    def decode_sals(data):
        return []


class InternalApplicationRegistrationTest(unittest.TestCase):

    def test_register_invalid_application(self):
        """Test registering invalid application IDs."""
        for a in (InvalidLowAppIDApplication, InvalidHighAppIDApplication):
            with self.assertRaises(ValueError):
                _register_application(a)
            for i in InvalidLowAppIDApplication.supported_applications():
                with self.assertRaises(KeyError):
                    get_application(int(i))

    def test_register_duplicate_application(self):
        """Test registering a different duplicate application ID."""
        with self.assertRaises(ValueError):
            _register_application(InvalidFakeLightingApplication)
        lighting = get_application(Application.LIGHTING)
        self.assertIsNot(lighting, InvalidFakeLightingApplication)

    def test_double_register_same(self):
        """Test registering an already-registered application ID."""
        # should not throw exception
        lighting = get_application(Application.LIGHTING)
        self.assertIsNot(lighting, InvalidFakeLightingApplication)
        _register_application(lighting)


if __name__ == '__main__':
    unittest.main()

