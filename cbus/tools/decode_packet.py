#!/usr/bin/env python
"""
cbus/tools/decode_packet.py - Attempt to decode a packet from a C-Bus network.
Copyright 2012 Michael Farrell <micolous+git@gmail.com>

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

from argparse import ArgumentParser
from cbus.protocol.packet import decode_packet


def pretty_packet(packet, checksum=True, strict=True, server_packet=True):
    packet, remainder = decode_packet(packet, checksum, strict, server_packet)

    print packet


def main():
    parser = ArgumentParser()

    parser.add_argument('packet',
                        metavar='PACKET',
                        nargs=1,
                        help='Packet to decode')

    parser.add_argument('-C',
                        '--no-checksum',
                        dest='checksum',
                        action='store_false',
                        help='Require a checksum on the packet')

    parser.add_argument('-S',
                        '--not-strict',
                        dest='strict',
                        action='store_false',
                        help='Strict mode')

    parser.add_argument(
        '-c',
        '--client',
        dest='server',
        action='store_false',
        help='Server to client packet (otherwise is client to server packet)')

    options = parser.parse_args()

    pretty_packet(options.packet[0], options.checksum, options.strict,
                  options.server)


if __name__ == '__main__':
    main()
