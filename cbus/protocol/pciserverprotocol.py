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
from base64 import b16encode, b16decode

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
		
		self._send('++', checksum=False)
		
		
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
		
		if line == '~~~':
			self.on_reset()

			return
		
		if len(line) == 0:
			# skip, empty line
			log.msg("recv: empty line")
			return
			
		# TODO: handle other bus requests properly.
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
		
		# check for any ? in the line (cancel), s4.2.4
		if '?' in line:
			# delete everything before the ?
			line = line[line.index('?')+1:]
			log.msg('recv: cancel, new request is %r' % line)
		
		# SMART + CONNECT shortcut
		if line == '|':
			self.basic_mode = False
			self.connect = True
			return
			
		if line[0] == '\\':
			# start of command message
			line = line[1:]
		
		event_string = line.strip()
		if event_string[-1] not in HEX_CHARS:
			# looks like a confirmation code
			confirmation_code = event_string[-1]
			event_string = event_string[:-1]
		else:
			confirmation_code = None
		
		for x in event_string:
			if x not in HEX_CHARS:
				# fail, invalid characters
				log.msg("invalid character %r in event %r, dropping event" % (x, event_string))
				self.send_error()
				return
		
		# check checksum
		if self.checksum:
			if validate_cbus_checksum(event_string):
				# checksum ok
				event_string = event_string[:-2]
			else:
				# checksum bad
				log.msg('recv: checksum bad!')
				self.send_error()
				return
			
			
		# decode string
		event_bytes = b16decode(event_string)
		
		event_code = ord(event_bytes[0])
		
		#if event_code >= 0xC0:
		#	# there is an MMI of length [0] - C0 (quick start page 13)
		#	event_length = ord(event_bytes[0]) - 0xC0
		#	event_data = event_bytes[1:event_length]
		#	
		#	# get the remainder
		#	event_bytes = event_bytes[event_length+1:]
		#	
		#	# parse information we know...
		#	application = ord(event_data[1])
		#	
		#	self.on_mmi(application, event_bytes)
		#	
		#	return event_bytes
		if event_code == 0xA3:
			# Serial parameter set
			# s10.2 Serial Interface Guide
			
			parameter = ord(event_bytes[1])
			reserved = ord(event_bytes[2])
			value = ord(event_bytes[3])
			
			if reserved != 0x00:
				log.msg('recv: parameter set reserved != 0 (%r)' % reserved)
				self.send_error()
				return
			
			if parameter == 0x21:
				# application address 1
				application_addr1 = value
			elif parameter == 0x22:
				# application address 2
				application_addr2 = value
			elif parameter == 0x3E:
				# interface options 2
				# TODO: implement
				pass
			elif parameter == 0x42:
				# interface options 3
				# TODO: implement
				pass
			elif parameter in (0x30, 0x41):
				# interface options 1 / power up options 1
				self.connect = self.checksum = self.monitor = self.idmon = False
				self.basic_mode = True
				
				if value & 0x01:
					self.connect = True
				if value & 0x02:
					# reserved, ignored.
					pass
				if value & 0x04:
					# TODO: xon/xoff handshaking.  not supported.
					pass
				if value & 0x08:
					# srchk (checksum checking)
					self.checksum = True
				if value & 0x10:
					# smart mode
					self.basic_mode = False
					self.local_echo = False
				if value & 0x20:
					# monitor mode
					self.monitor = True
				if value & 0x40:
					# idmon
					self.idmon = True

			#return
			
			
		elif event_code == 0x05:
			# this is a point to multipoint message
			#source_addr = ord(event_bytes[1])
			application = ord(event_bytes[1])
			routing = ord(event_bytes[2])
			
			
			if b16encode(chr(application)) == APP_LIGHTING:
				# lighting event.
				lighting_event = b16encode(event_bytes[3])
				group_addr = ord(event_bytes[4])
				
				if lighting_event in RAMP_RATES.keys():					
					duration = ramp_rate_to_duration(lighting_event)
					level = ord(event_bytes[5]) / 255.
					
					self.on_lighting_group_ramp(group_addr, duration, level)
					
					#return # event_bytes[7:]
				else:
					if lighting_event == LIGHT_ON:
						self.on_lighting_group_on(group_addr)
					elif lighting_event == LIGHT_OFF:
						self.on_lighting_group_off(group_addr)
					else:
						log.msg("unsupported lighting event: %r, dropping event %r" % (lighting_event, event_bytes))
						return
					
					#return #event_bytes[6:]
			else:
				# unknown application
				log.msg("unsupported PTMP application: %r, dropping event %r" % (application, event_bytes))
				return
		else:
			# unknown event
			log.msg("unsupported event code: %r, dropping event %r" % (event_code, event_bytes))
			return
		
		if confirmation_code:
			self.send_confirmation(confirmation_code, True)
	
	
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
	
	# other things.	
	
	def _send(self, cmd, checksum=True, nl=True):
		"""
		Sends a packet of CBus data.
		
		"""
		if checksum and self.checksum:
			cmd = add_cbus_checksum(cmd)
		
		log.msg("send: %r" % cmd)
		
		if nl:
			self.transport.write(cmd + END_COMMAND)
		else:
			self.transport.write(cmd)
		
	def send_error(self):
		self._send('!', checksum=False, nl=False)
	
	def send_confirmation(self, code, ok=True):
		if not ok:
			raise NotImplementedError, 'ok != true not implemented'
		
		self._send(code + '.', checksum=False, nl=False)
			
		
	
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
		if not validate_ga(group_addr):
			raise ValueError, 'group_addr out of range (%d - %d), got %r' % (MIN_GROUP_ADDR, MAX_GROUP_ADDR, group_addr)

		d = '05' + ('%02X' % source_addr) + APP_LIGHTING + ROUTING_NONE + LIGHT_ON + ('%02X' % group_addr)
		return self._send(d)
	
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
		if not validate_ga(group_addr):
			raise ValueError, 'group_addr out of range (%d - %d), got %r' % (MIN_GROUP_ADDR, MAX_GROUP_ADDR, group_addr)

		d = '05' + ('%02X' % source_addr) + APP_LIGHTING + ROUTING_NONE + LIGHT_OFF + ('%02X' % group_addr)
		return self._send(d)
	
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
		if not validate_ga(group_addr):
			raise ValueError, 'group_addr out of range (%d - %d), got %r' % (MIN_GROUP_ADDR, MAX_GROUP_ADDR, group_addr)
			
		if not (0.0 <= level <= 1.0):
			raise ValueError, 'Ramp level is out of bounds.  Must be between 0.0 and 1.0 (got %r).' % level
		
		if not validate_ramp_rate(duration):
			raise ValueError, 'Duration is out of bounds, must be between %d and %d (got %r)' % (MIN_RAMP_RATE, MAX_RAMP_RATE, duration)
		
		d = '05' + ('%02X' % source_addr) + APP_LIGHTING + ROUTING_NONE + LIGHT_OFF + \
			duration_to_ramp_rate(duration) + ('%02X%02X' % (group_addr, level))
		
		return self._send(d)
		
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
	

