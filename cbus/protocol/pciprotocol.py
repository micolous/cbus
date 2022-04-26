#!/usr/bin/env python
# cbus/protocol/pciprotocol.py - asyncio Protocol for C-Bus PCI/CNI
# Copyright 2012-2020 Michael Farrell <micolous+git@gmail.com>
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

from asyncio import (CancelledError, Future, Lock, create_task,
                     get_running_loop, run, sleep)
from asyncio.transports import WriteTransport
from datetime import datetime
import logging
from typing import Iterable, Optional, Text, Union

from six import int2byte

try:
    from serial_asyncio import create_serial_connection
except ImportError:
    async def create_serial_connection(*_, **__):
        raise ImportError('Serial device support requires pyserial-asyncio')

from cbus.common import (
    Application, CONFIRMATION_CODES, END_COMMAND, add_cbus_checksum)
from cbus.protocol.application.clock import (
    ClockSAL, ClockRequestSAL, ClockUpdateSAL, clock_update_sal)
from cbus.protocol.application.lighting import (
    LightingSAL, LightingOnSAL, LightingOffSAL, LightingRampSAL,
    LightingTerminateRampSAL)
from cbus.protocol.application.status_request import StatusRequestSAL
from cbus.protocol.base_packet import (
    BasePacket, SpecialServerPacket, SpecialClientPacket)
from cbus.protocol.cal.identify import IdentifyCAL
from cbus.protocol.cbus_protocol import CBusProtocol
from cbus.protocol.confirm_packet import ConfirmationPacket
from cbus.protocol.dm_packet import DeviceManagementPacket
from cbus.protocol.error_packet import PCIErrorPacket
# from cbus.protocol.po_packet import PowerOnPacket
from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.pp_packet import PointToPointPacket
from cbus.protocol.reset_packet import ResetPacket

logger = logging.getLogger(__name__)

__all__ = ['PCIProtocol']


class PCIProtocol(CBusProtocol):
    """
    Implements an asyncio Protocol for communicating with a C-Bus PCI/CNI over
    TCP or serial.

    """

    def __init__(
            self,
            timesync_frequency: int = 10,
            handle_clock_requests: bool = True,
            connection_lost_future: Optional[Future] = None):
        super(PCIProtocol, self).__init__(emulate_pci=False)

        self._transport = None  # type: Optional[WriteTransport]
        self._next_confirmation_index = 0
        self._recv_buffer = bytearray()
        self._recv_buffer_lock = Lock()
        self._timesync_frequency = timesync_frequency
        self._connection_lost_future = connection_lost_future
        self._handle_clock_requests = bool(handle_clock_requests)

    def connection_made(self, transport: WriteTransport) -> None:
        """
        Called by asyncio when a connection is made to the PCI.  This will
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

    def handle_cbus_packet(self, p: BasePacket) -> None:
        """
        Dispatches all packet types into a high level event handler.
        """

        if isinstance(p, SpecialServerPacket):
            if isinstance(p, PCIErrorPacket):
                self.on_pci_cannot_accept_data()
            elif isinstance(p, ConfirmationPacket):
                self.on_confirmation(p.code, p.success)
            else:
                logger.debug(f'hcp: unhandled SpecialServerPacket: {p!r}')
        elif isinstance(p, PointToMultipointPacket):
            for s in p:
                if isinstance(s, LightingSAL):
                    # lighting application
                    if isinstance(s, LightingRampSAL):
                        self.on_lighting_group_ramp(p.source_address,
                                                    s.group_address,s.application_address,
                                                    s.duration, s.level)
                    elif isinstance(s, LightingOnSAL):
                        self.on_lighting_group_on(p.source_address,
                                                  s.group_address,s.application_address)
                    elif isinstance(s, LightingOffSAL):
                        self.on_lighting_group_off(p.source_address,
                                                   s.group_address,s.application_address)
                    elif isinstance(s, LightingTerminateRampSAL):
                        self.on_lighting_group_terminate_ramp(
                            p.source_address, s.group_address,s.application_address)
                    else:
                        logger.debug(f'hcp: unhandled lighting SAL type: {s!r}')
                elif isinstance(s, ClockSAL):
                    if isinstance(s, ClockRequestSAL):
                        self.on_clock_request(p.source_address)
                    elif isinstance(s, ClockUpdateSAL):
                        self.on_clock_update(p.source_address, s.val)
                else:
                    logger.debug(f'hcp: unhandled SAL type: {s!r}')
        else:
            logger.debug(f'hcp: unhandled other packet: {p!r}')

    # event handlers
    def on_confirmation(self, code: bytes, success: bool):
        """
        Event called when a command confirmation event was received.

        :param code: A single byte matching the command that this is a response
                     to.

        :param success: True if the command was successful, False otherwise.
        """
        logger.debug(f'recv: confirmation: code = {code}, success = {success}')

    def on_reset(self):
        """
        Event called when the PCI has been hard reset.

        """
        logger.debug('recv: pci reset in progress!')

    def on_mmi(self, application: int, data: bytes):
        """
        Event called when a MMI was received.

        :param application: Application that this MMI concerns.
        :param data: MMI data

        """
        logger.debug(f'recv: mmi: application {application}, data {data!r}')

    def on_lighting_group_ramp(self, source_addr: int, group_addr: int,
                               duration: int, level: int):
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

        :param level: Target brightness of the ramp (0 - 255).
        :type level: int
        """
        logger.debug(
            f'recv: light ramp: from {source_addr} to {group_addr}, duration '
            f'{duration} seconds to level {level} ')

    def on_lighting_group_on(self, source_addr: int, group_addr: int):
        """
        Event called when a lighting application "on" request is received.

        :param source_addr: Source address of the unit that generated this
                            event.
        :type source_addr: int

        :param group_addr: Group address being turned on.
        :type group_addr: int
        """
        logger.debug(f'recv: light on: from {source_addr} to {group_addr}')

    def on_lighting_group_off(self, source_addr: int, group_addr: int):
        """
        Event called when a lighting application "off" request is received.

        :param source_addr: Source address of the unit that generated this
                            event.
        :type source_addr: int

        :param group_addr: Group address being turned off.
        :type group_addr: int
        """
        logger.debug(f'recv: light off: from {source_addr} to {group_addr}')

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
        logger.debug(
            f'recv: terminate ramp: from {source_addr} to {group_addr}')

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
        logger.debug(
            f'recv: lighting label text: from {source_addr} to {group_addr} '
            f'flavour {flavour} lang {language_code} text {label!r}')

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
        logger.debug('recv: PCI cannot accept data')

    def on_pci_power_up(self):
        """
        If Power-up Notification (PUN) is enabled on the PCI, this event is
        fired.

        This event may be fired multiple times in quick succession, as the PCI
        will send the event twice.

        """
        logger.debug('recv: PCI power-up notification')

    def on_clock_request(self, source_addr):
        """
        Event called when a unit requests time from the network.

        :param source_addr: Source address of the unit requesting time.
        :type source_addr: int
        """
        logger.debug(f'recv: clock request from {source_addr}')
        if self._handle_clock_requests:
            self.clock_datetime()

    def on_clock_update(self, source_addr, val):
        """
        Event called when a unit sends time to the network.

        :param source_addr: Source address of the unit requesting time.
        :type source_addr: int

        """
        logger.debug(f'recv: clock update from {source_addr} of {val!r}')

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
        transport = self._transport
        if transport is None:
            raise IOError('transport not connected')
        if not isinstance(cmd, BasePacket):
            raise TypeError('cmd must be BasePacket')
        logger.debug(f'send: {cmd!r}')

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

        cmd += END_COMMAND
        logger.debug(f'send: {cmd!r}')

        transport.write(cmd)
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
        # Set application address 1 to ALL applications
        # self._send('A32100FF', encode=False, checksum=False)
        self._send(DeviceManagementPacket(
            checksum=False, parameter=0x21, value=0xFF),
            basic_mode=True)
        
        # serial user interface guide sect 10.2
        # Set application address 2 to USED applications
        # self._send('A32200FF', encode=False, checksum=False)
        self._send(DeviceManagementPacket(
            checksum=False, parameter=0x22, value=0xFF),
            basic_mode=True)

        # Interface options #3
        # = 0x0E / 0000 1110
        # 1: LOCAL_SAL
        # 2: PUN - power-up notification
        # 3: EXSTAT
        # self._send('A342000E', encode=False, checksum=False)
        self._send(DeviceManagementPacket(
            checksum=False, parameter=0x42, value=0x0E),
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

    def lighting_group_on(self, group_addr: Union[int, Iterable[int]],application_addr: Union[int,Application] ):
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
            raise ValueError(
                f'group_addr iterable length is > 9 ({group_addr_count})')

        p = PointToMultipointPacket(
            sals=[LightingOnSAL(ga,application_addr) for ga in group_addr])
        return self._send(p)

    def lighting_group_off(self, group_addr: Union[int, Iterable[int]],application_addr: Union[int,Application] ):
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
            raise ValueError(
                f'group_addr iterable length is > 9 ({group_addr_count})')

        p = PointToMultipointPacket(
            sals=[LightingOffSAL(ga,application_addr) for ga in group_addr])
        return self._send(p)

    def lighting_group_ramp(
            self, group_addr: int, application_addr: Union[int,Application], duration: int, level: int = 255 ):
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
        :param level: A value between 0 and 255 indicating the brightness.
        :type level: int

        :returns: Single-byte string with code for the confirmation event.
        :rtype: string

        """
        p = PointToMultipointPacket(
            sals=LightingRampSAL(group_addr, application_addr, duration, level))
        return self._send(p)

    def lighting_group_terminate_ramp(
            self, group_addr: Union[int, Iterable[int]], application_addr: Union[int,Application]):
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
            raise ValueError(
                f'group_addr iterable length is > 9 ({group_addr_count})')

        p = PointToMultipointPacket(
            sals=[LightingTerminateRampSAL(ga,application_addr) for ga in group_addr])
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

        p = PointToMultipointPacket(sals=clock_update_sal(when))
        return self._send(p)

    async def timesync(self):
        frequency = self._timesync_frequency
        if frequency <= 0:
            return

        while True:
            try:
                self.clock_datetime()
                await sleep(frequency)
                # self._send(PointToMultipointPacket(sals=StatusRequestSAL(
                #     child_application=Application.LIGHTING,
                #     level_request=True,
                #     group_address=0,
                # )))
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
    from argparse import ArgumentParser

    parser = ArgumentParser(description="""\
        Test program that displays events from a connected C-Bus PCI (over 
        serial, USB or TCP) or CNI (TCP).
    """)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-s', '--serial',
        dest='serial', default=None, metavar='DEVICE',
        help='Serial port where the PCI is located. USB PCIs appear as a '
             'cp210x USB-serial adapter. (example: -s /dev/ttyUSB0)')

    group.add_argument(
        '-t', '--tcp',
        dest='tcp', default=None, metavar='ADDR:PORT',
        help='IP address and TCP port where the C-Bus CNI or PCI is located '
             '(eg: -t 192.0.2.1:10001)')

    option = parser.parse_args()

    global_logger = logging.getLogger('cbus')
    global_logger.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)
    loop = get_running_loop()
    connection_lost_future = loop.create_future()

    def factory():
        return PCIProtocol(connection_lost_future=connection_lost_future)

    if option.serial:
        await create_serial_connection(
            loop, factory, option.serial, baudrate=9600)
    elif option.tcp:
        addr, port = option.tcp.split(':', 2)
        await loop.create_connection(factory, addr, int(port))

    await connection_lost_future


if __name__ == '__main__':
    run(main())
