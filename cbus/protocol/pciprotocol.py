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
		
		if line[0] in CONFIRMATION_CODES:
			# this is blind, doesn't know if it was ok...
			success = line[1] == '.'
			
			self.on_confirmation(line[0], success)
			
			# shift across for the remainder
			line = line[2:]
		
		# TODO: handle other bus events properly.
	
	
	# event handlers
	def on_confirmation(self, code, success):
		log.msg("recv: confirmation: code = %r, success = %r" % (code, success))
	
	def on_reset(self):
		log.msg("recv: pci reset in progress!")
	
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
	

