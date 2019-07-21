#!/usr/bin/env python3
# cbus/protocol/pciserverprotocol.py - Twisted protocol implementation of the
# CBus PCI as a server.
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

import asyncio
import logging
import random
import sys
from typing import Text

from cbus.common import END_RESPONSE, Application, GroupState
from cbus.protocol.cal import AnyCAL
from cbus.protocol.cal.recall import RecallCAL
from cbus.protocol.cbus_protocol import CBusProtocol
from cbus.protocol.packet import decode_packet
from cbus.protocol.base_packet import (
    BasePacket, InvalidPacket, SpecialClientPacket)
from cbus.protocol.reset_packet import ResetPacket
from cbus.protocol.scs_packet import SmartConnectShortcutPacket
from cbus.protocol.po_packet import PowerOnPacket
from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.dm_packet import DeviceManagementPacket
from cbus.protocol.confirm_packet import ConfirmationPacket
from cbus.protocol.error_packet import PCIErrorPacket
from cbus.protocol.application.lighting import (
    LightingSAL, LightingRampSAL, LightingOffSAL, LightingOnSAL,
    LightingTerminateRampSAL)
from cbus.protocol.application.clock import (
    ClockSAL, ClockUpdateSAL, ClockRequestSAL)
from cbus.protocol.application.status_request import StatusRequestSAL
from cbus.protocol.cal.report import BinaryStatusReport
from cbus.protocol.cal.standard import StandardCAL

__all__ = ['PCIServerProtocol']
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PCIServerProtocol(CBusProtocol):
    """
    Implements a twisted protocol listening to CBus PCI commands over TCP or
    serial.

    This presently only implements a subset of the protocol used by
    PCIProtocol.

    """

    def __init__(self):
        super(PCIServerProtocol, self).__init__(server=True)
        self._transport = None

        self.basic_mode = True
        self.connect = False
        self.checksum = False
        self.monitor = False
        self.idmon = False

        self.application_addr1 = 0xff
        self.application_addr2 = 0xff
        self._send_queue = []

    def connection_made(self, transport):
        """
        Called by twisted a connection is made to the PCI.

        This doesn't get fired in normal serial connections, however we'll send
        a power up notification (PUN).

        Serial Interface User Guide s4.3.3.4, page 33

        """
        self._transport = transport
        self._send(PowerOnPacket())

    def echo(self, data: bytes) -> None:
        if self.basic_mode:
            self._transport.write(data)

    def handle_cbus_packet(self, p: BasePacket) -> None:
        """
        Handles a single CBus packet.

        """
        # check for special commands, and handle them.
        if p is None:
            logger.debug("dce: packet == None")
            return

        if isinstance(p, InvalidPacket):
            logger.warning("dce: invalid packet: {}".format(p.exception))
            return

        logger.debug('dce: %r', p)

        if isinstance(p, SpecialClientPacket):
            # do special things
            # full reset
            if isinstance(p, ResetPacket):
                self.on_reset()
                return

            # smart+connect shortcut
            if isinstance(p, SmartConnectShortcutPacket):
                self.basic_mode = False
                self.connect = True
                return

            logger.debug('dce: unknown SpecialClientPacket: %r', p)
        elif isinstance(p, RecallCAL):
            logger.debug('dce: got a cal?: %r', p)
            return
        elif isinstance(p, PointToMultipointPacket):
            for s in p:
                if isinstance(s, LightingSAL):
                    # lighting application
                    if isinstance(s, LightingRampSAL):
                        self.on_lighting_group_ramp(s.group_address,
                                                    s.duration, s.level)
                    elif isinstance(s, LightingOnSAL):
                        self.on_lighting_group_on(s.group_address)
                    elif isinstance(s, LightingOffSAL):
                        self.on_lighting_group_off(s.group_address)
                    elif isinstance(s, LightingTerminateRampSAL):
                        self.on_lighting_group_terminate_ramp(
                            s.group_address)
                    else:
                        logger.debug(
                            'dce: unhandled lighting SAL type: %r' % s)
                        return
                elif isinstance(s, ClockSAL):
                    if isinstance(s, ClockUpdateSAL):
                        self.on_clock_update(s.val)
                    elif isinstance(s, ClockRequestSAL):
                        self.on_clock_request()
                    else:
                        logger.debug(
                            'dce: unhandled clock SAL type: %r' % s)
                elif isinstance(s, StatusRequestSAL):
                    if (s.child_application == Application.MASTER_APPLICATION
                            and not s.level_request):
                        # s4.2.9.2 note: find presence of units
                        self.on_master_application_status(s.group_address)
                    else:
                        logger.debug(
                            'dce: unhandled status request SAL: %r', s)
                        return
                else:
                    logger.debug('dce: unhandled SAL type: %r' % s)
                    return
        elif isinstance(p, DeviceManagementPacket):
            # TODO: send proper confirmation, from p55 of serial interface
            #       guide
            if p.parameter == 0x21:
                # application address 1
                # TODO: implement
                pass
            elif p.parameter == 0x22:
                # application address 2
                # TODO: implement
                pass
            elif p.parameter == 0x3E:
                # interface options 2
                # TODO: implement
                pass
            elif p.parameter == 0x42:
                # interface options 3
                # TODO: implement
                pass
            elif p.parameter in (0x30, 0x41):
                # interface options 1 / power up options 1
                self.connect = self.checksum = False
                self.monitor = self.idmon = False
                self.basic_mode = True

                if p.value & 0x01:
                    self.connect = True
                if p.value & 0x02:
                    # reserved, ignored.
                    pass
                if p.value & 0x04:
                    # TODO: xon/xoff handshaking.  not supported.
                    pass
                if p.value & 0x08:
                    # srchk (checksum checking)
                    self.checksum = True
                if p.value & 0x10:
                    # smart mode
                    self.basic_mode = False
                if p.value & 0x20:
                    # monitor mode
                    self.monitor = True
                if p.value & 0x40:
                    # idmon
                    self.idmon = True
            else:
                logger.debug(
                    'dce: unhandled DeviceManagementPacket (%r = %r)' %
                    (p.parameter, p.value))
                return
        else:
            logger.debug('dce: unhandled packet type: %r', p)
            return

        # TODO: handle parameters

        if p.confirmation:
            self.send_confirmation(p.confirmation, True)

    # event handlers

    def on_reset(self):
        """
        Event called when the PCI has been hard reset.

        """

        # reset our state to default!
        logger.debug('recv: PCI hard reset')
        self.basic_mode = True
        self.idmon = self.connect = self.checksum = self.monitor = False
        self.application_addr1 = self.application_addr2 = 0xFF

    def on_lighting_group_ramp(self, group_addr, duration, level):
        """
        Event called when a lighting application ramp (fade) request is
        recieved.

        :param group_addr: Group address being ramped.
        :type group_addr: int

        :param duration: Duration, in seconds, that the ramp is occurring over.
        :type duration: int

        :param level: Target brightness of the ramp (0.0 - 1.0).
        :type level: float
        """
        logger.debug(
            "recv: lighting ramp: %d, duration %d seconds to level %.2f%%" %
            (group_addr, duration, level * 100))

    def on_lighting_group_on(self, group_addr):
        """
        Event called when a lighting application "on" request is recieved.

        :param group_addr: Group address being turned on.
        :type group_addr: int
        """
        logger.debug("recv: lighting on: %d" % group_addr)

    def on_lighting_group_off(self, group_addr):
        """
        Event called when a lighting application "off" request is recieved.

        :param group_addr: Group address being turned off.
        :type group_addr: int
        """
        logger.debug("recv: lighting off: %d" % group_addr)

    def on_lighting_group_terminate_ramp(self, group_addr):
        """
        Event called when a lighting application "terminate ramp" request is
        recieved.

        :param group_addr: Group address ramp being terminated.
        :type group_addr: int
        """
        logger.debug("recv: lighting terminate ramp: %d" % group_addr)

    def on_clock_request(self):
        """
        Event called when a clock application "request time" is recieved.
        """
        logger.debug("recv: clock request")

    def on_clock_update(self, val):
        """
        Event called when a clock application "update time" is recieved.

        :param variable: Clock variable to update.
        :type variable: int

        :param val: Clock value
        :type variable: datetime.date or datetime.time
        """
        logger.debug("recv: clock update: %r" % val)

        # DEBUG: randomly trigger lights
        p = PointToMultipointPacket(
            self.checksum, sals=LightingOnSAL(random.randint(1, 100)))
        p.source_address = random.randint(1, 100)

        self._send_later(p)

        p = PointToMultipointPacket(
            self.checksum, sals=LightingOffSAL(random.randint(1, 100)))
        p.source_address = random.randint(1, 100)
        self._send_later(p)

    def on_master_application_status(self, group_address: int) -> None:
        """
        Event called when a Status Request for the master application is called.

        This expects a binary status report of the presence of every unit on
        the network.
        :param group_address: Group number to start from
        """
        logger.debug(
            'recv: master application status request from %d', group_address)

        # TODO: implement this dynamically
        states = [GroupState.MISSING] + (
            [GroupState.ON] * 10
        ) + ([GroupState.MISSING] * (0xfe - 12)) + [GroupState.ON]
        assert len(states) >= 0xfe

        if self.basic_mode:
            for x in range(0, 0xff, 0x58):
                self._send(StandardCAL(
                    child_application=Application.MASTER_APPLICATION,
                    block_start=x,
                    report=BinaryStatusReport(states[x:][:0x58]),
                ))
        else:
            raise NotImplementedError('not implemented except basic mode')

    # other things.
    @staticmethod
    def _serialize_packet(cmd: BasePacket) -> bytes:
        nl = True
        if isinstance(cmd, ConfirmationPacket):
            nl = False

        cmd = cmd.encode_packet()
        if nl:
            cmd += END_RESPONSE

        return cmd

    def _send_later(self, cmd: BasePacket) -> None:
        self._send_queue.append(self._serialize_packet(cmd))

    def _send(self, cmd: BasePacket):
        """
        Sends a packet of CBus data.

        """
        cmd = self._serialize_packet(cmd)
        logger.debug("send: %r" % cmd)

        self._transport.write(cmd)

        # pull up the send queue
        send_queue = self._send_queue

        # remove the old one
        self._send_queue = []

        # send it all!
        for m in send_queue:
            self._transport.write(m)

    def send_error(self):
        self._send(PCIErrorPacket())

    def send_confirmation(self, code, ok=True):
        # if not ok:
        #   raise NotImplementedError, 'ok != true not implemented'

        self._send(ConfirmationPacket(code, ok))

    def lighting_group_on(self, source_addr, group_addr):
        """
        Turns on the lights for the given group_addr.

        :param source_addr: Source address of the event.
        :type source_addr: int

        :param group_addr: Group address to turn the lights on for.
        :type group_addr: int

        :returns: Single-byte string with code for the confirmation event.
        :rtype: string

        """

        p = PointToMultipointPacket(
            checksum=self.checksum,
            sals=LightingOnSAL(p, group_addr))
        p.source_address = source_addr
        return self._send(p)

    def lighting_group_off(self, source_addr, group_addr):
        """
        Turns off the lights for the given group_addr.

        :param source_addr: Source address of the event.
        :type source_addr: int

        :param group_addr: Group address to turn the lights on for.
        :type group_addr: int

        :returns: Single-byte string with code for the confirmation event.
        :rtype: string

        """
        p = PointToMultipointPacket(
            checksum=self.checksum,
            sals=LightingOffSAL(p, group_addr))
        p.source_address = source_addr
        return self._send(p)

    def lighting_group_ramp(
            self, source_addr, group_addr, duration, level=1.0):
        """
        Ramps (fades) a group address to a specified lighting level.

        Note: CBus only supports a limited number of fade durations, in
        decreasing accuracy up to 17 minutes (1020 seconds). Durations longer
        than this will throw an error.

        A duration of 0 will ramp "instantly" to the given level.

        :param source_addr: Source address of the event.
        :type source_addr: int

        :param group_addr: The group address to ramp.
        :type group_addr: int

        :param duration: Duration, in seconds, that the ramp should occur over.
        :type duration: int

        :param level: An amount between 0.0 and 1.0 indicating the brightness
                      to set.
        :type level: float

        :returns: Single-byte string with code for the confirmation event.
        :rtype: string

        """
        p = PointToMultipointPacket(
            checksum=self.checksum,
            sals=LightingRampSAL(p, group_addr, duration, level))
        return self._send(p)

    def lighting_group_terminate_ramp(self, source_addr, group_addr):
        """
        Stops ramping a group address at the current point.

        :param source_addr: Source address of the event.
        :type source_addr: int

        :param group_addr: Group address to stop ramping of.
        :type group_addr: int

        :returns: Single-byte string with code for the confirmation event.
        :rtype: string
        """
        p = PointToMultipointPacket(
            checksum=self.checksum,
            sals=LightingTerminateRampSAL(p, group_addr))
        p.source_address = source_addr
        return self._send(p)


async def main(address: Text = '127.0.0.1', port: int = 10001):
    print(f'Starting fake PCI on {address}:{port}')
    loop = asyncio.get_running_loop()
    server = await loop.create_server(
        lambda: PCIServerProtocol(),
        address, port)

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('address', nargs='?', default='127.0.0.1')
    parser.add_argument('port', nargs='?', default=10001, type=int)
    options = parser.parse_args()

    asyncio.run(main(options.address, options.port))
