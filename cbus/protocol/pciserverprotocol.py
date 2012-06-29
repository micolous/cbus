#!/usr/bin/env python
# cbus/protocol/pciserverprotocol.py - Twisted protocol implementation of the
# CBus PCI as a server.
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

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from twisted.internet import reactor
from cbus.common import *
from cbus.protocol.packet import decode_packet
from cbus.protocol.base_packet import BasePacket, SpecialClientPacket
from cbus.protocol.reset_packet import ResetPacket
from cbus.protocol.scs_packet import SmartConnectShortcutPacket
from cbus.protocol.po_packet import PowerOnPacket
from cbus.protocol.pm_packet import PointToMultipointPacket
from cbus.protocol.dm_packet import DeviceManagementPacket
from cbus.protocol.confirm_packet import ConfirmationPacket
from cbus.protocol.error_packet import PCIErrorPacket
from cbus.protocol.application.lighting import *

__all__ = ['PCIServerProtocol']

class PCIServerProtocol(LineReceiver):
	"""
	Implements a twisted protocol listening to CBus PCI commands over TCP or
	serial.
	
	This presently only implements a subset of the protocol used by PCIProtocol.
	
	"""

	delimiter = END_COMMAND
	local_echo = True
	basic_mode = True
	connect = False
	checksum = False
	monitor = False
	idmon = False
	
	application_addr1 = 0xFF
	application_addr2 = 0xFF
	
	
	def connectionMade(self):
		"""
		Called by twisted a connection is made to the PCI.
		
		This doesn't get fired in normal serial connections, however we'll send a
		power up notification (PUN).
		
		Serial Interface User Guide s4.3.3.4, page 33
		
		"""
		
		self._send(PowerOnPacket())
		
		
	def lineReceived(self, line):
		"""
		Called by LineReciever when a new line has been recieved on the
		PCI connection.
		
		Do not override this.
		
		:param line: Raw CBus event data
		:type line: str
		
		"""
		log.msg("recv: %r" % line)
		
		if self.basic_mode:
			self._send(line, checksum=False, nl=False)
		
		#if line == '~~~':
		#	self.on_reset()
		#	return
		#
		#if len(line) == 0:
		#	# skip, empty line
		#	log.msg("recv: empty line")
		#	return
			
		# TODO: handle other bus requests properly.
		while line:
			line = self.decode_cbus_event(line)
	
	def decode_cbus_event(self, line):
		"""
		Decodes a CBus event and calls an event handler appropriate to the event.
		
		Do not override this.
		
		:param line: CBus event data
		:type line: str
		
		:returns: Remaining unparsed data (str) or None on error.
		:rtype: str or NoneType
		
		"""
		
		# pass the data to the protocol decoder
		p, remainder = decode_packet(line, checksum=self.checksum, server_packet=False)
		
		# check for special commands, and handle them.
		if p == None:
			log.msg("dce: packet == None")
			return remainder
			
		if isinstance(p, SpecialClientPacket):
			# do special things
			# full reset
			if isinstance(p, ResetPacket):
				self.on_reset()
				return remainder
			
			# smart+connect shortcut
			if isinstance(p, SmartConnectShortcutPacket):
				self.basic_mode = False
				self.checksum = True
				self.connect = True
				return remainder
				
			log.msg('dce: unknown SpecialClientPacket: %r', p)
		elif isinstance(p, PointToMultipointPacket):
			# is this a status inquiry
			
			if p.status_request == None:
				# status request
				# TODO
				log.msg('dce: unhandled status request packet')
			else:
				# application command
				
				for s in p.sal:
					if isinstance(s, LightingSAL):
						# lighting application
						if isinstance(s, LightingRampSAL):
							self.on_lighting_group_ramp(s.group_address, s.duration, s.level)
						elif isinstance(s, LightingOnSAL):
							self.on_lighting_group_on(s.group_address)
						elif isinstance(s, LightingOffSAL):
							self.on_lighting_group_off(s.group_address)
						elif isinstance(s, LightingTerminateRampSAL):
							self.on_lighting_group_terminate_ramp(s.group_address)
						else:
							log.msg('dce: unhandled lighting SAL type: %r' % s)
							return remainder
					
					else:
						log.msg('dce: unhandled SAL type: %r' % s)
						return remainder
		elif isinstance(p, DeviceManagementPacket):
			if p.parameter == 0x21:
				# application address 1
				application_addr1 = p.value
			elif p.parameter == 0x22:
				# application address 2
				application_addr2 = p.value
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
				self.connect = self.checksum = self.monitor = self.idmon = False
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
					self.local_echo = False
				if p.value & 0x20:
					# monitor mode
					self.monitor = True
				if p.value & 0x40:
					# idmon
					self.idmon = True
			else:
				log.msg('dce: unhandled DeviceManagementPacket (%r = %r)' % (p.parameter, p.value))
				return remainder
		else:
			log.msg('dce: unhandled packet type: %r', p)
			return remainder
		
		# TODO: handle parameters
		
		if p.confirmation:
			self.send_confirmation(p.confirmation, True)
		
		return remainder
		
	# event handlers
	
	def on_reset(self):
		"""
		Event called when the PCI has been hard reset.
		
		"""
		
		# reset our state to default!
		log.msg('recv: PCI hard reset')
		self.local_echo = self.basic_mode = True
		self.idmon = self.connect = self.checksum = self.monitor = False
		self.application_addr1 = self.application_addr2 = 0xFF
		
	def on_lighting_group_ramp(self, group_addr, duration, level):
		"""
		Event called when a lighting application ramp (fade) request is recieved.
		
		:param group_addr: Group address being ramped.
		:type group_addr: int
		
		:param duration: Duration, in seconds, that the ramp is occurring over.
		:type duration: int
		
		:param level: Target brightness of the ramp (0.0 - 1.0).
		:type level: float
		"""
		log.msg("recv: lighting ramp: %d, duration %d seconds to level %.2f%%" % (group_addr, duration, level*100))
	
	def on_lighting_group_on(self, group_addr):
		"""
		Event called when a lighting application "on" request is recieved.
		
		:param group_addr: Group address being turned on.
		:type group_addr: int
		"""
		log.msg("recv: lighting on: %d" % (group_addr))
	
	def on_lighting_group_off(self, group_addr):
		"""
		Event called when a lighting application "off" request is recieved.
		
		:param group_addr: Group address being turned off.
		:type group_addr: int
		"""
		log.msg("recv: lighting off: %d" % (group_addr))
		
	def on_lighting_group_terminate_ramp(self, group_addr):
		"""
		Event called when a lighting application "terminate ramp" request is
		recieved.
		
		:param group_addr: Group address ramp being terminated.
		:type group_addr: int
		"""
		log.msg("recv: lighting terminate ramy: %d" % group_addr)
	
	# other things.	
	
	def _send(self, cmd, checksum=True, nl=True):
		"""
		Sends a packet of CBus data.
		
		"""
		if isinstance(cmd, BasePacket):
			checksum = False
			
			if isinstance(cmd, ConfirmationPacket):
				nl = False
			cmd = cmd.encode()
		else:
			if nl:
				# special packets get exemption from this warning
				log.msg('send: non-basepacket type!')
			if type(cmd) != str:
				# must be an iterable of ints
				cmd = ''.join([chr(x) for x in cmd])
		
		if checksum and self.checksum:
			cmd = add_cbus_checksum(cmd)
		
		log.msg("send: %r" % cmd)
		
		if nl:
			self.transport.write(cmd + END_COMMAND)
		else:
			self.transport.write(cmd)
		
	def send_error(self):
		self._send(PCIErrorPacket())
	
	def send_confirmation(self, code, ok=True):
		#if not ok:
		#	raise NotImplementedError, 'ok != true not implemented'
		
		self._send(ConfirmationPacket(code, ok))
			
		
	
	def lighting_group_on(self, source_addr, group_addr):
		"""
		Turns on the lights for the given group_id.
		
		:param source_addr: Source address of the event.
		:type source_addr: int
		
		:param group_id: Group address to turn the lights on for.
		:type group_id: int
		
		:returns: Single-byte string with code for the confirmation event.
		:rtype: string
		
		"""
		
		p = PointToMultipointPacket(application=APP_LIGHTING)
		p.source_address = source_addr
		p.sal.append(LightingOnSAL(p, group_addr))
		p.checksum = self.checksum
		return self._send(p)
	
	def lighting_group_off(self, source_addr, group_addr):
		"""
		Turns off the lights for the given group_id.
		
		:param source_addr: Source address of the event.
		:type source_addr: int	
		
		:param group_id: Group address to turn the lights on for.
		:type group_id: int
		
		:returns: Single-byte string with code for the confirmation event.
		:rtype: string
				
		"""
		p = PointToMultipointPacket(application=APP_LIGHTING)
		p.source_address = source_addr
		p.sal.append(LightingOffSAL(p, group_addr))
		p.checksum = self.checksum
		return self._send(p)

	
	def lighting_group_ramp(self, source_addr, group_addr, duration, level=1.0):
		"""
		Ramps (fades) a group address to a specified lighting level.

		Note: CBus only supports a limited number of fade durations, in decreasing
		accuracy up to 17 minutes (1020 seconds).  Durations longer than this will
		throw an error.
		
		A duration of 0 will ramp "instantly" to the given level.

		:param source_addr: Source address of the event.
		:type source_addr: int

		:param group_id: The group address to ramp.
		:type group_id: int
		
		:param duration: Duration, in seconds, that the ramp should occur over.
		:type duration: int
		
		:param level: An amount between 0.0 and 1.0 indicating the brightness to set.
		:type level: float
		
		:returns: Single-byte string with code for the confirmation event.
		:rtype: string
		
		"""
		p = PointToMultipointPacket(application=APP_LIGHTING)
		p.source_address = source_addr
		p.sal.append(LightingRampSAL(p, group_addr, duration, level))
		p.checksum = self.checksum
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
		p = PointToMultipointPacket(application=APP_LIGHTING)
		p.source_address = source_addr
		p.sal.append(LightingTerminateRampSAL(p, group_addr))
		p.checksum = self.checksum
		return self._send(p)

		
if __name__ == '__main__':
	# test program for protocol
	class PCIServerProtocolFactory(Factory):
		def buildProtocol(self, addr):
			log.msg('Connected.')
			return PCIServerProtocol()
	
	from twisted.internet import reactor
	
	import sys
	
	log.startLogging(sys.stdout)
	reactor.listenTCP(10001, PCIServerProtocolFactory())
	reactor.run()
	

