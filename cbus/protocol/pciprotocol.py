#!/usr/bin/env python
# cbus/protocol/pciprotocol.py - Twisted protocol implementation for CBus PCI
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
from __future__ import print_function

from asyncio import (CancelledError, Future, Lock, Protocol, create_task,
                     get_event_loop, run, sleep)
from asyncio.transports import BaseTransport
from datetime import datetime
from typing import Iterable, Optional, Text, Union

from six import int2byte
from twisted.python import log  # TODO: remove

from cbus.common import (
    CONFIRMATION_CODES, END_COMMAND, END_RESPONSE, MIN_MESSAGE_SIZE,
    MAX_BUFFER_SIZE, add_cbus_checksum)
from cbus.protocol.application.clock import (
    ClockSAL, ClockRequestSAL, ClockUpdateSAL)
from cbus.protocol.application.lighting import (
    LightingSAL, LightingOnSAL, LightingOffSAL, LightingRampSAL,
    LightingTerminateRampSAL)
from cbus.protocol.base_packet import (
    BasePacket, SpecialServerPacket, SpecialClientPacket)
from cbus.protocol.cal.identify import IdentifyCAL
from cbus.protocol.confirm_packet import ConfirmationPacket
from cbus.protocol.dm_packet import DeviceManagementPacket
from cbus.protocol.error_packet import PCIErrorPacket
from cbus.protocol.packet import decode_packet
# from cbus.protocol.po_packet import PowerOnPacket
from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.pp_packet import PointToPointPacket
from cbus.protocol.reset_packet import ResetPacket

__all__ = ['PCIProtocol']


class PCIProtocol(Protocol):
    """
    Implements a twisted protocol for communicating with a CBus PCI over serial
    or TCP.

    """

    def __init__(
            self,
            timesync_frequency: int = 10,
            handle_clock_requests: bool = True,
            connection_lost_future: Optional[Future] = None):
        self._transport = None  # type: Optional[BaseTransport]
        self._next_confirmation_index = 0
        self._recv_buffer = bytearray()
        self._recv_buffer_lock = Lock()
        self._timesync_frequency = timesync_frequency
        self._connection_lost_future = connection_lost_future
        self._handle_clock_requests = bool(handle_clock_requests)

    def connection_made(self, transport: BaseTransport) -> None:
        """
        Called by twisted when a connection is made to the PCI.  This will
        perform a reset of the PCI to establish the correct communications
        protocol, and start time synchronisation.

        """
        self._transport = transport
        self.pci_reset()
        if self._timesync_frequency:
            create_task(self.timesync())

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self._transport = None
        self._connection_lost_future.set_result(True)

    def data_received(self, data: bytes) -> None:
        """
        Called when there is new data from the PCI. Do not override this.

        :param data: Raw CBus event data
        """
        # log.msg("recv: %r" % data)
        create_task(self._data_received_async(data))

    async def _data_received_async(self, data: bytes) -> None:

        async with self._recv_buffer_lock:
            if len(self._recv_buffer) >= MAX_BUFFER_SIZE:
                log.msg(f'Buffer too big ({len(self._recv_buffer)} >= '
                        f'{MAX_BUFFER_SIZE}, truncating!')
                # Buffer too big, truncate it.
                eol = self._recv_buffer.find(END_RESPONSE)
                if eol == -1:
                    # reset buffer
                    self._recv_buffer = bytearray()
                else:
                    # shift buffer to where the next eol is
                    self._recv_buffer = self._recv_buffer[eol:]

            self._recv_buffer += data

            # Decode all waiting packets.
            while len(self._recv_buffer) >= MIN_MESSAGE_SIZE:
                p, remainder = decode_packet(
                    self._recv_buffer, checksum=True, server_packet=True)

                if remainder == 0:
                    # We don't have enough to do a proper decode yet, break!
                    return
                else:
                    self._recv_buffer = self._recv_buffer[remainder:]

                if p is None:
                    log.msg('dce: packet == None')
                    continue

                log.msg('dce: packet:', p)

                # Create a bunch of Tasks for handling these events,
                # so we don't need to hold the _recv_buffer_lock for too long.
                create_task(self.on_packet(p))

    async def on_packet(self, p: BasePacket) -> None:
        """
        Dispatches all packet types into a high level event handler.
        """

        if isinstance(p, SpecialServerPacket):
            if isinstance(p, PCIErrorPacket):
                self.on_pci_cannot_accept_data()
            elif isinstance(p, ConfirmationPacket):
                self.on_confirmation(p.code, p.success)
            else:
                log.msg('dce: unhandled SpecialServerPacket')
        elif isinstance(p, PointToMultipointPacket):
            for s in p:
                if isinstance(s, LightingSAL):
                    # lighting application
                    if isinstance(s, LightingRampSAL):
                        self.on_lighting_group_ramp(p.source_address,
                                                    s.group_address,
                                                    s.duration, s.level)
                    elif isinstance(s, LightingOnSAL):
                        self.on_lighting_group_on(p.source_address,
                                                  s.group_address)
                    elif isinstance(s, LightingOffSAL):
                        self.on_lighting_group_off(p.source_address,
                                                   s.group_address)
                    elif isinstance(s, LightingTerminateRampSAL):
                        self.on_lighting_group_terminate_ramp(
                            p.source_address, s.group_address)
                    else:
                        log.msg('dce: unhandled lighting SAL type', s)
                elif isinstance(s, ClockSAL):
                    if isinstance(s, ClockRequestSAL):
                        self.on_clock_request(p.source_address)
                    elif isinstance(s, ClockUpdateSAL):
                        self.on_clock_update(p.source_address, s.val)
                else:
                    log.msg('dce: unhandled SAL type', s)
        else:
            log.msg('dce: unhandled other packet', p)

    # event handlers
    def on_confirmation(self, code: bytes, success: bool):
        """
        Event called when a command confirmation event was received.

        :param code: A single byte matching the command that this is a response
                     to.
        :type code: str

        :param success: True if the command was successful, False otherwise.
        :type success: bool
        """
        log.msg('recv: confirmation: code = {}, success = {}'.format(
            code, success))

    def on_reset(self):
        """
        Event called when the PCI has been hard reset.

        """
        log.msg('recv: pci reset in progress!')

    def on_mmi(self, application: int, data: bytes):
        """
        Event called when a MMI was received.

        :param application: Application that this MMI concerns.
        :type application: int

        :param data: MMI data
        :type data: str

        """
        log.msg("recv: mmi: application %r, data %r" % (application, data))

    def on_lighting_group_ramp(self, source_addr: int, group_addr: int,
                               duration: int, level: float):
        """
        Event called when a lighting application ramp (fade) request is
        received.

        :param source_addr: Source address of the unit that generated this
                            event.
        :type source_addr: int

        :param group_addr: Group address being ramped.
        :type group_addr: int

        :param duration: Duration, in seconds, that the ramp is occurring over.
        :type duration: int

        :param level: Target brightness of the ramp (0.0 - 1.0).
        :type level: float
        """
        log.msg(
            'recv: lighting ramp: from {} to {}, duration {} seconds to level '
            '{:.2f}%'.format(source_addr, group_addr, duration, level * 100))

    def on_lighting_group_on(self, source_addr: int, group_addr: int):
        """
        Event called when a lighting application "on" request is received.

        :param source_addr: Source address of the unit that generated this
                            event.
        :type source_addr: int

        :param group_addr: Group address being turned on.
        :type group_addr: int
        """
        log.msg('recv: lighting on: from {} to {}'.format(
            source_addr, group_addr))

    def on_lighting_group_off(self, source_addr: int, group_addr: int):
        """
        Event called when a lighting application "off" request is received.

        :param source_addr: Source address of the unit that generated this
                            event.
        :type source_addr: int

        :param group_addr: Group address being turned off.
        :type group_addr: int
        """
        log.msg('recv: lighting off: from {} to {}'.format(
            source_addr, group_addr))

    def on_lighting_group_terminate_ramp(
            self, source_addr: int, group_addr: int):
        """
        Event called when a lighting application "terminate ramp" request is
        received.

        :param source_addr: Source address of the unit that generated this
                            event.
        :type source_addr: int

        :param group_addr: Group address stopping ramping.
        :type group_addr: int
        """
        log.msg('recv: lighting terminate ramp: from {} to {}'.format(
            source_addr, group_addr))

    def on_lighting_label_text(self, source_addr: int, group_addr: int,
                               flavour: int, language_code: int, label: Text):
        """
        Event called when a group address' label text is updated.

        :param source_addr: Source address of the unit that generated this
                            event.
        :type source_addr: int

        :param group_addr: Group address to relabel.
        :type group_addr: int

        :param flavour: "Flavour" of the label to update.  This is a value
                        between 0 and 3.
        :type flavour: int

        :param language_code: Language code for the label.
        :type language_code: int

        :param label: Label text, or an empty string to delete the label.
        :type label: str

        """
        log.msg(
            'recv: lighting label text: from {} to {} flavour {} lang {} '
            'text {}'.format(
                source_addr, group_addr, flavour, language_code, label))

    def on_pci_cannot_accept_data(self):
        """
        Event called whenever the PCI cannot accept the supplied data. Common
        reasons for this occurring:

        * The checksum is incorrect.
        * The buffer in the PCI is full.

        Unfortunately the PCI does not tell us which requests these are
        associated with.

        This error can occur if data is being sent to the PCI too quickly, or
        if the cable connecting the PCI to the computer is faulty.

        While the PCI can operate at 9600 baud, this only applies to data it
        sends, not to data it recieves.

        """
        log.msg("recv: PCI cannot accept data")

    def on_pci_power_up(self):
        """
        If Power-up Notification (PUN) is enabled on the PCI, this event is
        fired.

        This event may be fired multiple times in quick succession, as the PCI
        will send the event twice.

        """
        log.msg("recv: PCI power-up notification")

    def on_clock_request(self, source_addr):
        """
        Event called when a unit requests time from the network.

        :param source_addr: Source address of the unit requesting time.
        :type source_addr: int
        """
        log.msg('recv: clock request from %d' % (source_addr,))
        if self._handle_clock_requests:
            self.clock_datetime()

    def on_clock_update(self, source_addr, val):
        """
        Event called when a unit sends time to the network.

        :param source_addr: Source address of the unit requesting time.
        :type source_addr: int

        """
        log.msg('recv: clock update from %d of %r' % (source_addr, val))

    # other things.

    def _get_confirmation_code(self):
        """
        Creates a confirmation code, and increments forward the next in the
        list.

        """
        o = CONFIRMATION_CODES[self._next_confirmation_index]

        self._next_confirmation_index += 1
        self._next_confirmation_index %= len(CONFIRMATION_CODES)

        return int2byte(o)

    def _send(self,
              cmd: Union[BasePacket],
              confirmation: bool = True,
              basic_mode: bool = False):
        """
        Sends a packet of CBus data.

        """
        if not isinstance(cmd, BasePacket):
            raise TypeError('cmd must be BasePacket')

        checksum = False

        if isinstance(cmd, SpecialClientPacket):
            basic_mode = True
            confirmation = False

        cmd = cmd.encode_packet()

        if not basic_mode:
            cmd = b'\\' + cmd

        if checksum:
            cmd = add_cbus_checksum(cmd)

        if confirmation:
            conf_code = self._get_confirmation_code()
            cmd += conf_code

            # TODO: implement proper handling of confirmation codes.
        else:
            conf_code = None

        log.msg("send: %r" % cmd)

        self._transport.write(cmd + END_COMMAND)

        return conf_code

    def pci_reset(self):
        """
        Performs a full reset of the PCI.

        """
        # reset the PCI, disable MMI reports so we know when buttons are
        # pressed. (mmi toggle is 59g disable vs 79g enable)
        #
        # MMI calls aren't needed to get events from light switches and other
        # device on the network.

        # full system reset
        for _ in range(3):
            self._send(ResetPacket())

        # serial user interface guide sect 10.2
        # Set application address 1 to 38 (lighting)
        # self._send('A3210038', encode=False, checksum=False)
        self._send(DeviceManagementPacket(
            checksum=False, parameter=0x21, value=0x38),
            basic_mode=True)

        # Interface options #3 set to 02
        # "LOCAL_SAL".
        # self._send('A3420002', encode=False, checksum=False)
        self._send(DeviceManagementPacket(
            checksum=False, parameter=0x42, value=0x02),
            basic_mode=True)

        # Interface options #1
        # = 0x59 / 0101 1001
        # 0: CONNECT
        # 3: SRCHK - strict checksum check
        # 4: SMART
        # 5: MONITOR
        # 6: IDMON
        # self._send('A3300059', encode=False, checksum=False)
        self._send(DeviceManagementPacket(
            checksum=False, parameter=0x30, value=0x59),
            basic_mode=True)

    def identify(self, unit_address, attribute):
        """
        Sends an IDENTIFY command to the given unit_address.

        :param unit_address: Unit address to send the packet to
        :type unit_address: int

        :param attribute: Attribute ID to retrieve information for. See s7.2
                          of Serial Interface Guide for acceptable codes.
        :type attribute: int

        :returns: Single-byte string with code for the confirmation event.
        :rtype: string
        """
        p = PointToPointPacket(
            unit_address=unit_address, cals=[IdentifyCAL(attribute)])
        return self._send(p)

    def lighting_group_on(self, group_addr: Union[int, Iterable[int]]):
        """
        Turns on the lights for the given group_id.

        :param group_addr: Group address(es) to turn the lights on for, up to 9
        :type group_addr: int, or iterable of ints of length <= 9.

        :returns: Single-byte string with code for the confirmation event.
        :rtype: string

        """
        if not isinstance(group_addr, Iterable):
            group_addr = [group_addr]

        group_addr = [int(g) for g in group_addr]
        group_addr_count = len(group_addr)

        if group_addr_count > 9:
            # maximum 9 group addresses per packet
            raise ValueError('group_addr iterable length is > 9 ({})'.format(
                group_addr_count))

        p = PointToMultipointPacket(
            sals=[LightingOnSAL(ga) for ga in group_addr])
        return self._send(p)

    def lighting_group_off(self, group_addr: Union[int, Iterable[int]]):
        """
        Turns off the lights for the given group_id.

        :param group_addr: Group address(es) to turn the lights off for, up to
                           9
        :type group_addr: int, or iterable of ints of length <= 9.

        :returns: Single-byte string with code for the confirmation event.
        :rtype: string

        """
        if not isinstance(group_addr, Iterable):
            group_addr = [group_addr]

        group_addr = [int(g) for g in group_addr]
        group_addr_count = len(group_addr)

        if group_addr_count > 9:
            # maximum 9 group addresses per packet
            raise ValueError('group_addr iterable length is > 9 ({})'.format(
                group_addr_count))

        p = PointToMultipointPacket(
            sals=[LightingOffSAL(ga) for ga in group_addr])
        return self._send(p)

    def lighting_group_ramp(
            self, group_addr: int, duration: int, level: float = 1.0):
        """
        Ramps (fades) a group address to a specified lighting level.

        Note: CBus only supports a limited number of fade durations, in
        decreasing accuracy up to 17 minutes (1020 seconds). Durations
        longer than this will throw an error.

        A duration of 0 will ramp "instantly" to the given level.

        :param group_addr: The group address to ramp.
        :type group_addr: int
        :param duration: Duration, in seconds, that the ramp should occur over.
        :type duration: int
        :param level: A value between 0.0 and 1.0 indicating the brightness.
        :type level: float

        :returns: Single-byte string with code for the confirmation event.
        :rtype: string

        """
        p = PointToMultipointPacket(
            sals=LightingRampSAL(group_addr, duration, level))
        return self._send(p)

    def lighting_group_terminate_ramp(
            self, group_addr: Union[int, Iterable[int]]):
        """
        Stops ramping a group address at the current point.

        :param group_addr: Group address to stop ramping of.
        :type group_addr: int

        :returns: Single-byte string with code for the confirmation event.
        :rtype: string
        """

        if not isinstance(group_addr, Iterable):
            group_addr = [group_addr]

        group_addr = [int(g) for g in group_addr]
        group_addr_count = len(group_addr)

        if group_addr_count > 9:
            # maximum 9 group addresses per packet
            raise ValueError('group_addr iterable length is > 9 ({})'.format(
                group_addr_count))

        p = PointToMultipointPacket(
            sals=[LightingTerminateRampSAL(ga) for ga in group_addr])
        return self._send(p)

    def clock_datetime(self, when: Optional[datetime] = None):
        """
        Sends the system's local time to the CBus network.

        :param when: The time and date to send to the CBus network. Defaults
                     to current local time.
        :type when: datetime.datetime

        """
        if when is None:
            when = datetime.now()

        sals = [ClockUpdateSAL(when.date()), ClockUpdateSAL(when.time())]

        p = PointToMultipointPacket(sals=sals)
        return self._send(p)

    async def timesync(self):
        frequency = self._timesync_frequency
        if frequency <= 0:
            return

        while True:
            try:
                self.clock_datetime()
                await sleep(frequency)
            except CancelledError:
                break

    # def recall(self, unit_addr, param_no, count):
    #    return self._send('%s%02X%s%s%02X%02X' % (
    #        POINT_TO_46, unit_addr, ROUTING_NONE, RECALL, param_no, count
    #    ))

    # def identify(self, unit_addr, attribute):
    #    return self._send('%s%02X%s%s%02X' % (
    #        POINT_TO_46, unit_addr, ROUTING_NONE, RECALL, attribute
    #    ))


async def main():
    """
    Test program for PCIProtocol.

    Imports are included inside of this method in order to avoid loading
    unneeded dependencies.
    """
    import sys

    from argparse import ArgumentParser
    from serial_asyncio import create_serial_connection

    parser = ArgumentParser(description="""\
        Library for communications with a CBus PCI in Twisted.  Acts as a test
        program to dump events from a PCI.
    """)
    parser.add_argument(
        '-s', '--serial-pci',
        dest='serial_pci', default=None,
        help='Serial port where the PCI is located. Either this or -t must be '
             'specified.')

    parser.add_argument(
        '-t', '--tcp-pci',
        dest='tcp_pci', default=None,
        help='IP address and TCP port where the PCI is located (CNI). Either '
             'this or -s must be specified.')

    option = parser.parse_args()

    log.startLogging(sys.stdout)
    loop = get_event_loop()
    connection_lost_future = loop.create_future()

    if option.serial_pci and option.tcp_pci:
        return parser.error(
            'Both serial and TCP CBus PCI addresses were specified! Use only '
            'one...')
    elif option.serial_pci:
        await create_serial_connection(
            loop,
            lambda: PCIProtocol(connection_lost_future=connection_lost_future),
            option.serial_pci, baudrate=9600)
    elif option.tcp_pci:
        # TODO
        addr = option.tcp_pci.split(':', 2)
        await loop.create_connection(
            lambda: PCIProtocol(connection_lost_future=connection_lost_future),
            addr[0], int(addr[1]))
    else:
        return parser.error(
            'No CBus PCI address was specified!  (See -s or -t option)')

    await connection_lost_future


if __name__ == '__main__':
    run(main())
