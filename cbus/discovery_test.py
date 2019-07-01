#!/usr/bin/env python
"""
cbus/discovery_test.py - experiments with CNI discovery
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

http://stackoverflow.com/a/3632240


"""

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from base64 import b16encode, b16decode
import socket

CBUS_DISCOVERY_QUERY = '\xcb\x80\0\0'
CBUS_DISCOVERY_REPLY = '\xcb\x81\0\0'


class CNIDiscoveryProtocol(DatagramProtocol):

    def __init__(self):
        self.transport = reactor.listenUDP(20050, self)
        self.transport.getHandle().setsockopt(socket.SOL_SOCKET,
                                              socket.SO_BROADCAST, 1)

    def startProtocol(self):
        "Called when transport is connected"
        pass

    def stopProtocol(self):
        "called after the transport is teared down"
        pass

    def datagramReceived(self, data, (host, port)):
        print "Recieved datagram from %s:%d:" % (host, port)
        print b16encode(data)

        # now determine what kind of message this is.
        message_type = data[:4]

        if message_type == CBUS_DISCOVERY_QUERY:
            # discovery message
            print "Query Message."

            # respond to it with a standard message.
            d = b16decode(
                'CB810000' +  # CBUS_DISCOVERY_REPLY
                #'00000005' +
                '20E8F552' + '81010001' + '05'
                +  # 01 == CNI2, 02 == invalid (doesn't show in toolkit), 03 == WISER, 04 == "unknown"
                '810B0002' + '2721' +  # port  (uint16 big endian)
                '811D0001' + '00' +  # unknown
                '80010002661E')
            self.write(d, host, port)

        elif message_type == CBUS_DISCOVERY_REPLY:
            print "Reply message."
        else:
            print "Unhandled message type."

        print

    def write(self, data, ip, port):
        # we need to send responses to the IP/port that sent it.
        print "Sending message to %s:%d" % (ip, port)
        print b16encode(data)

        self.transport.getHandle().sendto(data, (ip, port))
        print


if __name__ == '__main__':
    print "listening"
    CNIDiscoveryProtocol()
    reactor.run()
