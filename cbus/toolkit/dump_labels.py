#!/usr/bin/env python
"""
toolkit/dump_labels.py
Dumps group address and unit metadata from a Toolkit CBZ.

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
from argparse import ArgumentParser
import json
import sys

from cbus.toolkit.cbz import CBZ


def main():
    parser = ArgumentParser(
        usage='%prog -i input.cbz -o output.json')
    parser.add_argument(
        '-o', '--output', metavar='FILE',
        help='write output to FILE')
    parser.add_argument(
        'input', nargs=1, metavar='FILE',
        help='read Toolkit backup from FILE')
    parser.add_argument(
        '-p', '--pretty',
        type=int, required=False, metavar='SPACES',
        help='pretty-prints the output with the specified number of spaces '
             'between indent levels'
    )
    options = parser.parse_args()


    pretty = None
    if options.pretty:
        try:
            pretty = int(options.pretty)
        except ValueError:
            parser.error('Pretty-printing spaces value is not a number.')
            return

        if pretty < 0:
            parser.error('Pretty-printing spaces value must not be negative.')
            return

    cbz = CBZ(options.input[0])
    if options.output is None:
        of = sys.stdout
    else:
        of = open(options.output, 'w')

    # read in the labels we need into a structure.
    o = {}

    # iterate through networks
    for network in cbz.installation.project.network:
        no = {
            'name': network.tag_name,
            'address': network.address,
            'networknumber': network.network_number,
            # don't worry about converting CNI/PCI parameters.
            'applications': {},
            'units': {}
        }
        for application in network.applications:
            ao = {
                'name': application.tag_name,
                'address': application.address,
                'description': application.description,
                'groups': {}
            }

            for group in application.groups:
                ao['groups'][group.address] = group.tag_name

            no['applications'][application.address] = ao

        for unit in network.units:
            # find the channel configuration
            channels = []
            for parameter in unit.pp:
                if parameter.name == 'GroupAddress':
                    ch = parameter.value.split(' ')
                    [
                        channels.append(
                            int('0%s' % (c[2:]) if len(c) == 3 else (c[2:]),
                                16)) for c in ch
                    ]

                    # print channels
                    # print(parameter.attrib['Name'], '=',
                    #       parameter.attrib['Value'])
            no['units'][unit.address] = {
                'name': unit.tag_name,
                'address': unit.address,
                'unittype': unit.unit_type,
                'unitname': unit.unit_name,
                'serial': unit.serial_number,
                'catalog': unit.catalog_number,
                'groups': channels
            }

        o[network.address] = no

    # dump structure as json.
    json.dump(o, of, indent=pretty)
    of.flush()
    of.close()


if __name__ == '__main__':
    main()
