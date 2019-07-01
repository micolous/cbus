#!/usr/bin/env python
"""
cbus/toolkit/cbz.py
Library for reading CBus Toolkit CBZ files with lxml.

Copyright 2012-2019 Michael Farrell <micolous+git@gmail.com>

This library is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this library.  If not, see <http://www.gnu.org/licenses/>.
"""

from zipfile import ZipFile
from lxml import objectify


class CBZException(Exception):
    pass


class CBZ(object):

    def __init__(self, fh):
        """
        Opens the file as a CBZ.

        fh can either be a string poining to a file name or a file-like object.
        """
        self.zip = ZipFile(fh, 'r')
        files = self.zip.namelist()

        if len(files) != 1:
            raise CBZException('The number of files in this archive is not 1.')

        # validate the filename.
        xmlfilename = files[0]
        if not xmlfilename.endswith('.xml'):
            raise CBZException(
                'The file in this archive does not have a .xml extension. '
                'It is probably not a CBZ.')

        # now open the inner file and objectify.
        self.tree = objectify.parse(self.zip.open(xmlfilename, 'r'))
        self.root = self.tree.getroot()
