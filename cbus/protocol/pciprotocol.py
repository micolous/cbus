#!/usr/bin/env python
"""
cbus/protocol/pciprotocol.py - Twisted protocol implementation for the CBus PCI.
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
"""

from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from twisted.internet import reactor
from cbus.common import *
from base64 import b16encode, b16decode

class PCIProtocol(LineReceiver):
	delimiter = END_COMMAND
	next_confirmation_index = 0
	processing_events = False
	
	def connectionMade(self):
		# fired when there is a connection made to the server endpoint
		self.pci_reset()
		
	def lineReceived(self, line):
		log.msg("recv: %r" % line)
		
		if line == '~~~':
			self.on_reset()
			return
		
		if line[0] in CONFIRMATION_CODES:
			# this is blind, doesn't know if it was ok...
			success = line[1] == '.'
			
			self.on_confirmation(line[0], success)
			
			# shift across for the remainder
			line = line[2:]
		
		# TODO: handle other bus events properly.
		self.decode_cbus_event(line)
	
	def decode_cbus_event(self, line):
		"""
		returns a remaining unparsed data, or None on error (ie: discard result)
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
	
	
	# event handlers
	def on_confirmation(self, code, success):
		log.msg("recv: confirmation: code = %r, success = %r" % (code, success))
	
	def on_reset(self):
		log.msg("recv: pci reset in progress!")
		
	def on_mmi(self, application, bytes):
		log.msg("recv: mmi: application %r, data %r" % (application, bytes))
		
	def on_lighting_group_ramp(self, source_addr, group_addr, duration, level):
		log.msg("recv: lighting ramp: from %d to %d, duration %d seconds to level %.2f%%" % (source_addr, group_addr, duration, level*100))
	
	def on_lighting_group_on(self, source_addr, group_addr):
		log.msg("recv: lighting on: from %d to %d" % (source_addr, group_addr))
	
	def on_lighting_group_off(self, source_addr, group_addr):
		log.msg("recv: lighting off: from %d to %d" % (source_addr, group_addr))
	
	
	# other things.	
	
	def _get_confirmation_code(self):
		"""
		Creates a confirmation code, and increments forward the next in the list.
		
		"""
		o = CONFIRMATION_CODES[self.next_confirmation_index]
		
		self.next_confirmation_index += 1
		self.next_confirmation_index %= len(CONFIRMATION_CODES)
		
		return o
	
	def send(self, cmd, checksum=True, confirmation=True):
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
		# reset the PCI, disable MMI reports so we know when buttons are pressed.
		# (mmi toggle is 59g disable vs 79g enable)
		# 
		# MMI calls aren't needed to get events from light switches and other device on the network.
		
		# full system reset
		self.send('~~~', checksum=False, confirmation=False)
		
		# serial user interface guide sect 10.2
		# Set application address 1 to 38 (lighting)
		self.send('A3210038', checksum=False)
		
		# Interface options #3 set to 02
		# "Reserved".
		self.send('A3420002', checksum=False)
		
		# Interface options #1
		# = 0x59 / 0101 1001
		# 0: CONNECT
		# 3: SRCHK - strict checksum check
		# 4: SMART
		# 5: MONITOR
		# 6: IDMON
		self.send('A3300059', checksum=False)
	
	def lighting_group_on(self, group_addr):
		if not (MIN_GROUP_ADDR <= group_addr <= MAX_GROUP_ADDR):
			raise ValueError, 'group_addr out of range (%d - %d), got %r' % (MIN_GROUP_ADDR, MAX_GROUP_ADDR, group_addr)

		d = POINT_TO_MULTIPOINT + APP_LIGHTING + ROUTING_NONE + LIGHT_ON + ('%02X' % group_addr)
		return self.send(d)
	
	def lighting_group_off(self, group_addr):
		if not (MIN_GROUP_ADDR <= group_addr <= MAX_GROUP_ADDR):
			raise ValueError, 'group_addr out of range (%d - %d), got %r' % (MIN_GROUP_ADDR, MAX_GROUP_ADDR, group_addr)

		d = POINT_TO_MULTIPOINT + APP_LIGHTING + ROUTING_NONE + LIGHT_OFF + ('%02X' % group_addr)
		return self.send(d)
	
	def lighting_group_ramp(self, group_addr, duration, level=1.0):
		if not (MIN_GROUP_ADDR <= group_addr <= MAX_GROUP_ADDR):
			raise ValueError, 'group_addr out of range (%d - %d), got %r' % (MIN_GROUP_ADDR, MAX_GROUP_ADDR, group_addr)
			
		if not (0.0 <= level <= 1.0):
			raise ValueError, 'Ramp level is out of bounds.  Must be between 0.0 and 1.0 (got %r).' % level
		
		if not (MIN_RAMP_RATE <= duration <= MAX_RAMP_RATE):
			raise ValueError, 'Duration is out of bounds, must be between %d and %d (got %r)' % (MIN_RAMP_RATE, MAX_RAMP_RATE, duration)
		
		d = POINT_TO_MULTIPOINT + APP_LIGHTING + ROUTING_NONE + LIGHT_OFF + \
			duration_to_ramp_rate(duration) + ('%02X%02X' % (group_addr, level))
		
		return self.send(d)
	
	def recall(self, unit_addr, param_no, count):
		return self.send('%s%02X%s%s%02X%02X' % (
			POINT_TO_46, unit_addr, ROUTING_NONE, RECALL, param_no, count
		))
		

	
	def identify(self, unit_addr, attribute):
		return self.send('%s%02X%s%s%02X' % (
			POINT_TO_46, unit_addr, ROUTING_NONE, RECALL, attribute
		))
		
		
		
		

if __name__ == '__main__':
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
	

