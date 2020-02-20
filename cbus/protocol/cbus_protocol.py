#!/usr/bin/env python3
# cbus/protocol/cbus_protocol.py
# CBus protocol decoder
# Copyright 2019-2020 Michael Farrell <micolous+git@gmail.com>
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

from cbus.common import MAX_BUFFER_SIZE
from cbus.protocol.buffered_protocol import BufferedProtocol
from cbus.protocol.packet import decode_packet
from cbus.protocol.base_packet import BasePacket

logger = logging.getLogger(__name__)

__all__ = ['CBusProtocol']


class CBusProtocol(BufferedProtocol, abc.ABC):
    """
    A CBus protocol handler.

    """

    def __init__(self, emulate_pci: bool = True):
        """
        :param emulate_pci: If True, this protocol handler will implement
            some of the low-level primitives to emulate a PCI; all
            incoming data will be parsed as if it were sent from software
            expecting to communicate with an actual PCI, and it will emulate
            local echo. Checksums are not required by default.

            If False, this protocol handler will act as if it is
            communicating _with_ a PCI; incoming data will be parsed as if it
            were sent by a PCI. Checksums are required by default.
        """
        super(CBusProtocol, self).__init__(size_limit=MAX_BUFFER_SIZE)
        self.emulate_pci = bool(emulate_pci)  # type: bool
        self.checksum = not self.emulate_pci  # type: bool

    def handle_data(self, buf: bytes) -> int:
        """
        Decodes a single CBus event and calls an event handler appropriate to
        the event.

        Do not override this.

        :param buf: CBus event data
        :type buf: bytes

        :returns: Number of bytes consumed from the buffer
        """
        logger.debug("Incoming data: %r", buf)

        p, remainder = decode_packet(
            buf, checksum=self.checksum, from_pci=not self.emulate_pci)

        if self.emulate_pci and remainder > 0:
            # Local echo
            self.echo(buf[:remainder])

        if p is not None:
            logger.debug("Got packet: %s", p)
            self.handle_cbus_packet(p)

        return remainder

    @abc.abstractmethod
    def handle_cbus_packet(self, p: BasePacket) -> None:
        """
        Called when there is a new packet available to be processed.

        :param p: Packet to process.
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
