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
		
		if line == '~~~':
			self.on_reset()
			return
		
		while line[0] == '!':
			# buffer is full / invalid checksum, some requests have been dropped!
			# (serial interface guide s4.3.3; page 28)
			self.on_pci_cannot_accept_data()
			line = line[1:]
		
		while line[0] in CONFIRMATION_CODES:
			# this is blind, doesn't know if it was ok...
			success = line[1] == '.'
			
			self.on_confirmation(line[0], success)
			
			# shift across for the remainder
			line = line[2:]
		
		# TODO: handle other bus events properly.
		self.decode_cbus_event(line)
	
	def decode_cbus_event(self, line):
		"""
		Decodes a CBus event and calls an event handler appropriate to the event.
		
		Do not override this.
		
		:param line: CBus event data
		:type line: str
		
		:returns: Remaining unparsed data (str) or None on error.
		:rtype: str or NoneType
		
		"""
		event_string = line.strip()
		for x in event_string:
			if x not in HEX_CHARS:
				# fail, invalid characters
				log.msg("invalid character %r in event %r, dropping event" % (x, event_string))
				return
				
		# decode string
		event_bytes = b16decode(event_string)
		
		event_code = ord(event_bytes[0])
		
		if event_code >= 0xC0:
			# there is an MMI of length [0] - C0 (quick start page 13)
			event_length = ord(event_bytes[0]) - 0xC0
			event_data = event_bytes[1:event_length]
			
			# get the remainder
			event_bytes = event_bytes[event_length+1:]
			
			# parse information we know...
			application = ord(event_data[1])
			
			self.on_mmi(application, event_bytes)
			
			return event_bytes
		elif event_code == 0x05:
			# this is a point to multipoint message
			source_addr = ord(event_bytes[1])
			application = ord(event_bytes[2])
			routing = ord(event_bytes[3])
			
			
			if b16encode(chr(application)) == APP_LIGHTING:
				# lighting event.
				lighting_event = b16encode(event_bytes[4])
				group_addr = ord(event_bytes[5])
				
				if lighting_event in RAMP_RATES.keys():
					checksum = ord(event_bytes[7])
					
					duration = ramp_rate_to_duration(lighting_event)
					level = ord(event_bytes[6]) / 255.
					
					self.on_lighting_group_ramp(source_addr, group_addr, duration, level)
					
					return event_bytes[8:]
				else:
					checksum = ord(event_bytes[6])
					if lighting_event == LIGHT_ON:
						self.on_lighting_group_on(source_addr, group_addr)
					elif lighting_event == LIGHT_OFF:
						self.on_lighting_group_off(source_addr, group_addr)
					else:
						log.msg("unsupported lighting event: %r, dropping event %r" % (self.lighting_event, event_bytes))
						return
					
					return event_bytes[7:]
			else:
				# unknown application
				log.msg("unsupported PTMP application: %r, dropping event %r" % (application, event_bytes))
				return
		else:
			# unknown event
			log.msg("unsupported event code: %r, dropping event %r" % (event_code, event_bytes))
			return
	
	
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
		log.msg("recv: lighting ramp: from %d to %d, duration %d seconds to level %.2f%%" % (source_addr, group_addr, duration, level*100))
	
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
	
	# other things.	
	
	def _get_confirmation_code(self):
		"""
		Creates a confirmation code, and increments forward the next in the list.
		
		"""
		o = CONFIRMATION_CODES[self._next_confirmation_index]
		
		self._next_confirmation_index += 1
		self._next_confirmation_index %= len(CONFIRMATION_CODES)
		
		return o
	
	def _send(self, cmd, checksum=True, confirmation=True):
		"""
		Sends a packet of CBus data.
		
		"""
		if checksum:
			cmd = add_cbus_checksum(cmd)
			
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
		self._send('~~~', checksum=False, confirmation=False)
		
		# serial user interface guide sect 10.2
		# Set application address 1 to 38 (lighting)
		self._send('A3210038', checksum=False)
		
		# Interface options #3 set to 02
		# "Reserved".
		self._send('A3420002', checksum=False)
		
		# Interface options #1
		# = 0x59 / 0101 1001
		# 0: CONNECT
		# 3: SRCHK - strict checksum check
		# 4: SMART
		# 5: MONITOR
		# 6: IDMON
		self._send('A3300059', checksum=False)
	
	def lighting_group_on(self, group_addr):
		"""
		Turns on the lights for the given group_id.
		
		:param group_id: Group address to turn the lights on for.
		:type group_id: int
		:returns: Single-byte string with code for the confirmation event.
		:rtype: string
		
		"""
		if not validate_ga(group_addr):
			raise ValueError, 'group_addr out of range (%d - %d), got %r' % (MIN_GROUP_ADDR, MAX_GROUP_ADDR, group_addr)

		d = POINT_TO_MULTIPOINT + APP_LIGHTING + ROUTING_NONE + LIGHT_ON + ('%02X' % group_addr)
		return self._send(d)
	
	def lighting_group_off(self, group_addr):
		"""
		Turns off the lights for the given group_id.
		
		:param group_id: Group address to turn the lights on for.
		:type group_id: int
		:returns: Single-byte string with code for the confirmation event.
		:rtype: string
		
		
		"""
		if not validate_ga(group_addr):
			raise ValueError, 'group_addr out of range (%d - %d), got %r' % (MIN_GROUP_ADDR, MAX_GROUP_ADDR, group_addr)

		d = POINT_TO_MULTIPOINT + APP_LIGHTING + ROUTING_NONE + LIGHT_OFF + ('%02X' % group_addr)
		return self._send(d)
	
	def lighting_group_ramp(self, group_addr, duration, level=1.0):
		"""
		Ramps (fades) a group address to a specified lighting level.

		Note: CBus only supports a limited number of fade durations, in decreasing
		accuracy up to 17 minutes (1020 seconds).  Durations longer than this will
		throw an error.
		
		A duration of 0 will ramp "instantly" to the given level.

		:param group_id: The group address to ramp.
		:type group_id: int
		:param duration: Duration, in seconds, that the ramp should occur over.
		:type duration: int
		:param level: An amount between 0.0 and 1.0 indicating the brightness to set.
		:type level: float
		
		:returns: Single-byte string with code for the confirmation event.
		:rtype: string
		
		"""
		if not validate_ga(group_addr):
			raise ValueError, 'group_addr out of range (%d - %d), got %r' % (MIN_GROUP_ADDR, MAX_GROUP_ADDR, group_addr)
			
		if not (0.0 <= level <= 1.0):
			raise ValueError, 'Ramp level is out of bounds.  Must be between 0.0 and 1.0 (got %r).' % level
		
		if not validate_ramp_rate(duration):
			raise ValueError, 'Duration is out of bounds, must be between %d and %d (got %r)' % (MIN_RAMP_RATE, MAX_RAMP_RATE, duration)
		
		d = POINT_TO_MULTIPOINT + APP_LIGHTING + ROUTING_NONE + LIGHT_OFF + \
			duration_to_ramp_rate(duration) + ('%02X%02X' % (group_addr, level))
		
		return self._send(d)
	
	def recall(self, unit_addr, param_no, count):
		return self._send('%s%02X%s%s%02X%02X' % (
			POINT_TO_46, unit_addr, ROUTING_NONE, RECALL, param_no, count
		))
		

	
	def identify(self, unit_addr, attribute):
		return self._send('%s%02X%s%s%02X' % (
			POINT_TO_46, unit_addr, ROUTING_NONE, RECALL, attribute
		))
		
if __name__ == '__main__':
	# test program for protocol
	class PCIProtocolFactory(ClientFactory):
		def startedConnecting(self, connector):
			log.msg('Started to connect')
	
		def buildProtocol(self, addr):
			log.msg('Connected.')
			return PCIProtocol()
		
		def clientConnectionLost(self, connector, reason):
			print 'Lost connection.  Reason:', reason

		def clientConnectionFailed(self, connector, reason):
			print 'Connection failed. Reason:', reason
	
	from twisted.internet import reactor
	from twisted.internet.serialport import SerialPort
	import sys
	
	log.startLogging(sys.stdout)
	SerialPort(PCIProtocol(), '/dev/ttyUSB0', reactor, baudrate=9600)
	reactor.run()
	

