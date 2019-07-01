#!/usr/bin/env python
# cbus/protocol/pciprotocol.py - Twisted protocol implementation for the CBus PCI.
# Copyright 2012 Michael Farrell <micolous+git@gmail.com>
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

from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from twisted.internet import reactor
from cbus.common import *
from base64 import b16encode, b16decode
from traceback import print_exc
from collections import Iterable
from cbus.protocol.packet import decode_packet
from cbus.protocol.base_packet import BasePacket, SpecialServerPacket, SpecialClientPacket
from cbus.protocol.po_packet import PowerOnPacket
from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.pp_packet import PointToPointPacket
from cbus.protocol.dm_packet import DeviceManagementPacket
from cbus.protocol.confirm_packet import ConfirmationPacket
from cbus.protocol.error_packet import PCIErrorPacket
from cbus.protocol.application.lighting import *
from cbus.protocol.application.clock import *
from cbus.protocol.cal.identify import *
from cbus.protocol.reset_packet import ResetPacket
from datetime import datetime

__all__ = ['PCIProtocol']


class PCIProtocol(LineReceiver):
    """
	Implements a twisted protocol for communicating with a CBus PCI over serial
	or TCP.
	
	"""

    delimiter = END_COMMAND
    _next_confirmation_index = 0

    def connectionMade(self):
        """
		Called by twisted a connection is made to the PCI.  This will perform a
		reset of the PCI to establish the correct communications protocol.
		
		"""
        # fired when there is a connection made to the server endpoint
        self.pci_reset()

    def lineReceived(self, line):
        """
		Called by LineReciever when a new line has been recieved on the
		PCI connection.
		
		Do not override this.
		
		:param line: Raw CBus event data
		:type line: str
		
		"""
        log.msg("recv: %r" % line)

        try:
            self.decode_cbus_event(line)
        except Exception:
            # caught exception.  dump stack trace to log and move on
            log.msg("recv: caught exception. line state = %r" % line)
            print_exc()

    def decode_cbus_event(self, line):
        """
		Decodes a CBus event and calls an event handler appropriate to the event.
		
		Do not override this.
		
		:param line: CBus event data
		:type line: str
		
		:returns: Remaining unparsed data (str) or None on error.
		:rtype: str or NoneType
		
		"""

        while line:
            last_line = line
            p, line = decode_packet(line, checksum=True, server_packet=True)

            if line == last_line:
                # infinite loop!
                log.msg('dce: bug: infinite loop detected on %r', line)
                return

            # decode special packets
            if p == None:
                log.msg("dce: packet == None")
                continue

            log.msg('dce: packet: %r' % p)

            if isinstance(p, SpecialServerPacket):
                if isinstance(p, PCIErrorPacket):
                    self.on_pci_cannot_accept_data()
                    continue
                elif isinstance(p, ConfirmationPacket):
                    self.on_confirmation(p.code, p.success)
                    continue

                log.msg('dce: unhandled SpecialServerPacket')
            elif isinstance(p, PointToMultipointPacket):
                for s in p.sal:
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
                            log.msg('dce: unhandled lighting SAL type: %r', s)
                            break
                    elif isinstance(s, ClockSAL):
                        if isinstance(s, ClockRequestSAL):
                            self.on_clock_request(p.source_address)
                        elif isinstance(s, ClockUpdateSAL):
                            self.on_clock_update(p.source_address, s.variable,
                                                 s.val)
                    else:
                        log.msg('dce: unhandled SAL type: %r', s)
                        break

            else:
                log.msg('dce: unhandled other packet %r', p)
                continue

    # event handlers
    def on_confirmation(self, code, success):
        """
		Event called when a command confirmation event was recieved.
		
		:param code: A single byte matching the command that this is a response to.
		:type code: str
		
		:param success: True if the command was successful, False otherwise.
		:type success: bool
		"""
        log.msg("recv: confirmation: code = %r, success = %r" % (code, success))

    def on_reset(self):
        """
		Event called when the PCI has been hard reset.
		
		"""
        log.msg("recv: pci reset in progress!")

    def on_mmi(self, application, bytes):
        """
		Event called when a MMI was recieved.
		
		:param application: Application that this MMI concerns.
		:type application: int
		
		:param bytes: MMI data
		:type bytes: str
		
		"""
        log.msg("recv: mmi: application %r, data %r" % (application, bytes))

    def on_lighting_group_ramp(self, source_addr, group_addr, duration, level):
        """
		Event called when a lighting application ramp (fade) request is recieved.
		
		:param source_addr: Source address of the unit that generated this event.
		:type source_addr: int
		
		:param group_addr: Group address being ramped.
		:type group_addr: int
		
		:param duration: Duration, in seconds, that the ramp is occurring over.
		:type duration: int
		
		:param level: Target brightness of the ramp (0.0 - 1.0).
		:type level: float
		"""
        log.msg(
            "recv: lighting ramp: from %d to %d, duration %d seconds to level %.2f%%"
            % (source_addr, group_addr, duration, level * 100))

    def on_lighting_group_on(self, source_addr, group_addr):
        """
		Event called when a lighting application "on" request is recieved.
		
		:param source_addr: Source address of the unit that generated this event.
		:type source_addr: int
		
		:param group_addr: Group address being turned on.
		:type group_addr: int
		"""
        log.msg("recv: lighting on: from %d to %d" % (source_addr, group_addr))

    def on_lighting_group_off(self, source_addr, group_addr):
        """
		Event called when a lighting application "off" request is recieved.
		
		:param source_addr: Source address of the unit that generated this event.
		:type source_addr: int
		
		:param group_addr: Group address being turned off.
		:type group_addr: int
		"""
        log.msg("recv: lighting off: from %d to %d" % (source_addr, group_addr))

    def on_lighting_group_terminate_ramp(self, source_addr, group_addr):
        """
		Event called when a lighting application "terminate ramp" request is
		recieved.
		
		:param source_addr: Source address of the unit that generated this event.
		:type source_addr: int
		
		:param group_addr: Group address stopping ramping.
		:type group_addr: int
		"""
        log.msg("recv: lighting terminate ramp: from %d to %d" %
                (source_addr, group_addr))

    def on_lighting_label_text(self, source_addr, group_addr, flavour,
                               language_code, label):
        """
		Event called when a group address' label text is updated.
		
		:param source_addr: Source address of the unit that generated this event.
		:type source_addr: int
		
		:param group_addr: Group address to relabel.
		:type group_addr: int
		
		:param flavour: "Flavour" of the label to update.  This is a value between 0 and 3.
		:type flavour: int
		
		:param language_code: Language code for the label.
		:type language_code: int
		
		:param event_bytes: Label text, or an empty string to delete the label.
		:type event_bytes: str
		
		
		"""
        log.msg(
            "recv: lighting label text: from %d to %d flavour %d lang %d text %r"
            % (source_addr, group_addr, flavour, language_code, label))

    def on_pci_cannot_accept_data(self):
        """
		Event called whenever the PCI cannot accept the supplied data.  Common
		reasons for this occurring:
		
		* The checksum is incorrect.
		* The buffer in the PCI is full.
		
		Unfortunately the PCI does not tell us which requests these are associated
		with.
		
		This error can occur if data is being sent to the PCI too quickly, or if 
		the cable connecting the PCI to the computer is faulty.
		
		While the PCI can operate at 9600 baud, this only applies to data it
		sends, not to data it recieves.
		
		"""
        log.msg("recv: PCI cannot accept data")

    def on_pci_power_up(self):
        """
		If Power-up Notification (PUN) is enabled on the PCI, this event is fired.
		
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

    def on_clock_update(self, source_addr, variable, val):
        """
		Event called when a unit sends time to the network.

		:param source_addr: Source address of the unit requesting time.
		:type source_addr: int
		
		"""
        log.msg('recv: clock update from %d of %r' % (source_addr, val))

    # other things.

    def _get_confirmation_code(self):
        """
		Creates a confirmation code, and increments forward the next in the list.
		
		"""
        o = CONFIRMATION_CODES[self._next_confirmation_index]

        self._next_confirmation_index += 1
        self._next_confirmation_index %= len(CONFIRMATION_CODES)

        return o

    def _send(self,
              cmd,
              encode=True,
              checksum=True,
              confirmation=True,
              basic_mode=False):
        """
		Sends a packet of CBus data.
		
		"""
        if isinstance(cmd, BasePacket):
            encode = checksum = False

            if isinstance(cmd, SpecialClientPacket):
                basic_mode = True
                confirmation = False

            cmd = cmd.encode()

            if not basic_mode:
                cmd = '\\' + cmd
        else:
            log.msg('send: cmd is not BasePacket!')
            if type(cmd) != str:
                # must be an iterable of ints
                cmd = ''.join([chr(x) for x in cmd])

        if checksum:
            cmd = add_cbus_checksum(cmd)

        if encode:
            cmd = '\\' + b16encode(cmd)

        if confirmation:
            conf_code = self._get_confirmation_code()
            cmd += conf_code

            # TODO: implement proper handling of confirmation codes.

        log.msg("send: %r" % cmd)

        self.transport.write(cmd + END_COMMAND)

        if confirmation:
            return conf_code

    def pci_reset(self):
        """
		Performs a full reset of the PCI.
		
		"""
        # reset the PCI, disable MMI reports so we know when buttons are pressed.
        # (mmi toggle is 59g disable vs 79g enable)
        #
        # MMI calls aren't needed to get events from light switches and other device on the network.

        # full system reset
        self._send(ResetPacket())

        # serial user interface guide sect 10.2
        # Set application address 1 to 38 (lighting)
        #self._send('A3210038', encode=False, checksum=False)
        self._send(DeviceManagementPacket(checksum=False,
                                          parameter=0x21,
                                          value=0x38),
                   basic_mode=True)

        # Interface options #3 set to 02
        # "LOCAL_SAL".
        #self._send('A3420002', encode=False, checksum=False)
        self._send(DeviceManagementPacket(checksum=False,
                                          parameter=0x42,
                                          value=0x02),
                   basic_mode=True)

        # Interface options #1
        # = 0x59 / 0101 1001
        # 0: CONNECT
        # 3: SRCHK - strict checksum check
        # 4: SMART
        # 5: MONITOR
        # 6: IDMON
        #self._send('A3300059', encode=False, checksum=False)
        self._send(DeviceManagementPacket(checksum=False,
                                          parameter=0x30,
                                          value=0x59),
                   basic_mode=True)

    def identify(self, unit_address, attribute):
        """
		Sends an IDENTIFY command to the given unit_address.
		
		:param unit_address: Unit address to send the packet to
		:type unit_address: int
		
		:param attribute: Attribute ID to retrieve information for.  See s7.2 of Serial Interface Guide for acceptable codes.
		:type attribute: int
		
		:returns: Single-byte string with code for the confirmation event.
		:rtype: string
		"""
        p = PointToPointPacket(unit_address=unit_address)
        p.cal.append(IdentifyCAL(p, attribute))

        return self._send(p)

    def lighting_group_on(self, group_addr):
        """
		Turns on the lights for the given group_id.
		
		:param group_addr: Group address(es) to turn the lights on for, up to 9.
		:type group_addr: int, or iterable of ints of length <= 9.
		
		:returns: Single-byte string with code for the confirmation event.
		:rtype: string
		
		"""
        if not isinstance(group_addr, Iterable):
            group_addr = [group_addr]

        group_addr = [int(g) for g in group_addr]

        if len(group_addr) > 9:
            # maximum 9 group addresses per packet
            raise ValueError, 'group_addr iterable length is > 9 (%r)' % len(
                group_addr)

        p = PointToMultipointPacket(application=APP_LIGHTING)
        for ga in group_addr:
            p.sal.append(LightingOnSAL(p, ga))

        return self._send(p)

    def lighting_group_off(self, group_addr):
        """
		Turns off the lights for the given group_id.
		
		:param group_addr: Group address(es) to turn the lights off for, up to 9.
		:type group_addr: int, or iterable of ints of length <= 9.
		
		:returns: Single-byte string with code for the confirmation event.
		:rtype: string
		
		"""
        if not isinstance(group_addr, Iterable):
            group_addr = [group_addr]

        group_addr = [int(g) for g in group_addr]

        if len(group_addr) > 9:
            # maximum 9 group addresses per packet
            raise ValueError, 'group_addr iterable length is > 9 (%r)' % len(
                group_addr)

        p = PointToMultipointPacket(application=APP_LIGHTING)
        for ga in group_addr:
            p.sal.append(LightingOffSAL(p, ga))

        return self._send(p)

    def lighting_group_ramp(self, group_addr, duration, level=1.0):
        """
		Ramps (fades) a group address to a specified lighting level.

		Note: CBus only supports a limited number of fade durations, in decreasing
		accuracy up to 17 minutes (1020 seconds).  Durations longer than this will
		throw an error.
		
		A duration of 0 will ramp "instantly" to the given level.

		:param group_addr: The group address to ramp.
		:type group_addr: int
		:param duration: Duration, in seconds, that the ramp should occur over.
		:type duration: int
		:param level: An amount between 0.0 and 1.0 indicating the brightness to set.
		:type level: float
		
		:returns: Single-byte string with code for the confirmation event.
		:rtype: string
		
		"""
        p = PointToMultipointPacket(application=APP_LIGHTING)
        p.sal.append(LightingRampSAL(p, group_addr, duration, level))
        return self._send(p)

    def lighting_group_terminate_ramp(self, group_addr):
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

        if len(group_addr) > 9:
            # maximum 9 group addresses per packet
            raise ValueError, 'group_addr iterable length is > 9 (%r)' % len(
                group_addr)

        p = PointToMultipointPacket(application=APP_LIGHTING)
        for ga in group_addr:
            p.sal.append(LightingTerminateRampSAL(p, ga))

        return self._send(p)

    def clock_datetime(self, when=None):
        """
		Sends the system's local time to the CBus network.

		:param when: The time and date to send to the CBus network.  Defaults to current local time.
		:type when: datetime.datetime
		
		"""
        if when == None:
            when = datetime.now()

        p = PointToMultipointPacket(application=APP_CLOCK)

        p.sal.append(ClockUpdateSAL(p, CLOCK_DATE, when.date()))
        p.sal.append(ClockUpdateSAL(p, CLOCK_TIME, when.time()))

        return self._send(p)

    #def recall(self, unit_addr, param_no, count):
    #	return self._send('%s%02X%s%s%02X%02X' % (
    #		POINT_TO_46, unit_addr, ROUTING_NONE, RECALL, param_no, count
    #	))

    #def identify(self, unit_addr, attribute):
    #	return self._send('%s%02X%s%s%02X' % (
    #		POINT_TO_46, unit_addr, ROUTING_NONE, RECALL, attribute
    #	))


if __name__ == '__main__':
    # test program for protocol
    from twisted.internet import reactor
    from twisted.internet.serialport import SerialPort
    import sys
    from optparse import OptionParser
    from twisted.internet.endpoints import TCP4ClientEndpoint
    from twisted.internet.protocol import Factory

    class PCIProtocolFactory(ClientFactory):

        def startedConnecting(self, connector):
            log.msg('Started to connect')

        def buildProtocol(self, addr):
            log.msg('Connected.')
            return PCIProtocol()

        def clientConnectionLost(self, connector, reason):
            print 'Lost connection.  Reason:', reason
            reactor.stop()

        def clientConnectionFailed(self, connector, reason):
            print 'Connection failed. Reason:', reason
            reactor.stop()

    class CBusProtocolHandlerFactory(Factory):

        def __init__(self, protocol):
            self.protocol = protocol

        def buildProtocol(self, addr):
            return self.protocol

    parser = OptionParser(usage='%prog',
                          description="""
		Library for communications with a CBus PCI in Twisted.  Acts as a test
		program to dump events from a PCI.
	""")
    parser.add_option(
        '-s',
        '--serial-pci',
        dest='serial_pci',
        default=None,
        help=
        'Serial port where the PCI is located.  Either this or -t must be specified.'
    )
    parser.add_option(
        '-t',
        '--tcp-pci',
        dest='tcp_pci',
        default=None,
        help=
        'IP address and TCP port where the PCI is located (CNI).  Either this or -s must be specified.'
    )

    option, args = parser.parse_args()

    log.startLogging(sys.stdout)

    protocol = PCIProtocol()
    if option.serial_pci and option.tcp_pci:
        parser.error(
            'Both serial and TCP CBus PCI addresses were specified!  Use only one...'
        )
    elif option.serial_pci:
        SerialPort(protocol, option.serial_pci, reactor, baudrate=9600)
    elif option.tcp_pci:
        addr = option.tcp_pci.split(':', 2)
        point = TCP4ClientEndpoint(reactor, addr[0], int(addr[1]))
        d = point.connect(CBusProtocolHandlerFactory(protocol))
    else:
        parser.error(
            'No CBus PCI address was specified!  (See -s or -t option)')

    reactor.run()
