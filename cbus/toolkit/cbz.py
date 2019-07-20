#!/usr/bin/env python
"""
cbus/toolkit/cbz.py
Library for reading CBus Toolkit CBZ files.

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

from __future__ import absolute_import

import dataclasses
from datetime import datetime
from typing import Any, BinaryIO, Sequence, Optional, Union, Text, \
    Type, TypeVar
from uuid import UUID
from xml.etree import ElementTree
from zipfile import ZipFile


BaseCBZElementType = TypeVar('BaseCBZElementType', bound='BaseCBZElement')
C_co = TypeVar('C_co', covariant=True)
T = TypeVar('T')


def _new(typ: Type) -> Any:
    if typ == type(None):
        return None
    # TODO: implement better
    if repr(typ).startswith('typing.Sequence'):
        return list()

    # default to None
    return None


@dataclasses.dataclass
class _Element:
    @staticmethod
    def _normalise_name(name: Text):
        return name.lower().replace('_', '')

    @classmethod
    def from_element(cls: Type[BaseCBZElementType],
                     element: ElementTree.Element) -> BaseCBZElementType:
        params = {}

        fields = dataclasses.fields(cls)
        field_names = [cls._normalise_name(n.name) for n in fields]

        # Initialise Optional and Lists
        for field in fields:
            params[field.name] = _new(field.type)

        # Read all attributes on the class
        for key, value in element.items():
            key = cls._normalise_name(key)

            try:
                findex = field_names.index(key)
            except ValueError:
                # no match
                continue

            field = fields[findex]
            params[field.name] = field.type(value)

        # Read all children
        for i in range(len(element)):
            # Use __getitem__ because we want to only go one level,
            # and exclude self.
            child = element[i]
            key = cls._normalise_name(child.tag)

            try:
                findex = field_names.index(key)
            except ValueError:
                # no match
                continue

            field = fields[findex]
            # HACK: get subscripted type from Sequence[]
            if isinstance(params[field.name], list):
                child_type = field.type.__args__[0]
            else:
                child_type = field.type

            if issubclass(child_type, BaseCBZElement):
                # Delegate parsing for child
                value = child_type.from_element(child)
            elif child_type == datetime:
                value = datetime.fromisoformat(child.text)
            else:
                value = child_type(child.text)

            if isinstance(params[field.name], list):
                params[field.name].append(value)
            else:
                params[field.name] = value

        # We have all we need...
        return cls(**params)


@dataclasses.dataclass
class PP(_Element):
    name: Text
    value: Text


@dataclasses.dataclass
class BaseCBZElement(_Element):
    oid: UUID


@dataclasses.dataclass
class BaseNetworkElement(BaseCBZElement):
    tag_name: Text
    address: int


@dataclasses.dataclass
class Interface(BaseCBZElement):
    interface_type: Text
    interface_address: Text


@dataclasses.dataclass
class Unit(BaseNetworkElement):
    unit_type: Text
    unit_name: Text
    serial_number: Text
    firmware_version: Text
    catalog_number: Text
    pp: Sequence[PP]


@dataclasses.dataclass
class Level(BaseNetworkElement):
    value: int


@dataclasses.dataclass
class Group(BaseNetworkElement):
    levels: Sequence[Level]


@dataclasses.dataclass
class Application(BaseNetworkElement):
    groups: Sequence[Group]


@dataclasses.dataclass
class Network(BaseNetworkElement):
    description: Text
    network_number: int
    interface: Interface
    applications: Sequence[Application]
    units: Sequence[Unit]


@dataclasses.dataclass
class Project(BaseCBZElement):
    tag_name: Text
    address: Text
    description: Text
    network: Sequence[Network]


@dataclasses.dataclass
class Installer(BaseCBZElement):
    name: Text


@dataclasses.dataclass
class InstallationDetail(BaseCBZElement):
    system_location: Text
    hardware_platform: Text
    hostname: Text
    os_name: Text
    os_version: Text
    hardware_location: Text
    installer: Installer


@dataclasses.dataclass
class Installation(BaseCBZElement):
    db_version: Text
    version: Text
    modified: datetime
    installation_detail: InstallationDetail
    project: Project


class CBZException(Exception):
    pass


class CBZ(object):

    def __init__(self, fh: Union[BinaryIO, Text]):
        """
        Opens the file as a CBZ.

        fh can either be a string poining to a file name or a file-like object.
        """
        self.zip = ZipFile(fh, 'r')
        files = self.zip.namelist()

        if len(files) != 1:
            raise CBZException(
                f'Expected 1 file in CBZ archive, got {len(files)}')

        # validate the filename.
        xmlfilename = files[0]
        if not xmlfilename.endswith('.xml'):
            raise CBZException(
                'The file in this archive does not have a .xml extension. '
                'It is probably not a CBZ.')

        # now open the inner file and objectify.
        self._tree = ElementTree.parse(
            self.zip.open(xmlfilename, 'r')).getroot()
        self.installation = Installation.from_element(self._tree)
