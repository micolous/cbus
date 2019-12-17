#!/usr/bin/env python
# test_common.py - Common functionality unit tests
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

from cbus.common import add_cbus_checksum


class CommonTest(unittest.TestCase):

    def test_cbus_checksum(self):
        """Test that adding a cbus checksum works for every byte value."""
        for x in range(256):
            b = bytes([x])
            c = bytes([x, ((x ^ 0xff) + 1) & 0xff])
            self.assertEqual(c, add_cbus_checksum(b), f'bad checksum for {x}')

    def test_empty_checksum(self):
        self.assertEqual(b'\0', add_cbus_checksum(b''))


if __name__ == '__main__':
    unittest.main()
