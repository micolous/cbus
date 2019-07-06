#!/usr/bin/env python3
# cbus/protocol/cbus_protocol.py
# CBus protocol decoder
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

import abc
import logging

from cbus.protocol.buffered_protocol import BufferedProtocol
from cbus.protocol.packet import decode_packet
from cbus.protocol.base_packet import BasePacket

logger = logging.getLogger(__name__)

__all__ = ['CBusProtocol']


class CBusProtocol(BufferedProtocol, abc.ABC):
    """
    A CBus protocol handler.

    """

    def __init__(self, server: bool = False):
        """
        :param server: True if this is a server.
        """
        super(CBusProtocol, self).__init__()
        self.server = server
        if server:
            self.checksum = False
        else:
            self.checksum = True

    def handle_data(self, buf: bytes) -> int:
        """
        Decodes a single CBus event and calls an event handler appropriate to
        the event.

        Do not override this.

        :param buf: CBus event data
        :type buf: bytes

        :returns: Number of bytes consumed from the buffer
        """
        # pass the data to the protocol decoder
        p, remainder = decode_packet(
            buf, checksum=self.checksum, server_packet=not self.server)

        if self.server and remainder > 0:
            # Local echo
            self.echo(buf[:remainder])

        if p is not None:
            self.handle_cbus_packet(p)

        return remainder

    @abc.abstractmethod
    def handle_cbus_packet(self, packet: BasePacket) -> None:
        """
        Called when there is a new packet available to be processed.

        :param packet: Packet to process.
        :return: ignored
        """
        pass

    def echo(self, data: bytes) -> None:
        """
        Called when data needs to be echoed to the underlying transport.

        This is only called when running in server mode.

        The default implementation is a stub, and needs to be implemented
        when running in server mode. This should only do something if the
        virtual PCI is in ``basic`` mode.
        """
        pass
