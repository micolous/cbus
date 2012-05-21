#!/usr/bin/env python
"""
libcbus/base.py - Base CBus libcbus framework.
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
from libcbus.common import *

class CBusBase(object):
	"""
	Generic CBus module.
	
	You should subclass this to implement a libcbus implementation that doesn't
	talk over CBus serial protocol.  If your protocol uses the serial protocol,
	you should use CBusPCI instead.
	
	This module by default does input validation and nothing else.
	
	"""
	
	def lighting_group_on(self, group_id):
		"""
		Turns on the lights for the given group_id.
		
		:param group_id: Group address to turn the lights on for.
		:type group_id: int
		:returns: Single-byte string with code for the confirmation event.
		:rtype: string
		
		"""
		if not (MIN_GROUP_ADDR <= group_id <= MAX_GROUP_ADDR):
			raise ValueError, 'group_id out of range (%d - %d), got %r' % (MIN_GROUP_ADDR, MAX_GROUP_ADDR, group_id)
				
	def lighting_group_off(self, group_id):
		"""
		Turns off the lights for the given group_id.
		
		:param group_id: Group address to turn the lights on for.
		:type group_id: int
		:returns: Single-byte string with code for the confirmation event.
		:rtype: string
		
		
		"""
		if not (MIN_GROUP_ADDR <= group_id <= MAX_GROUP_ADDR):
			raise ValueError, 'group_id out of range (%d - %d), got %r' % (MIN_GROUP_ADDR, MAX_GROUP_ADDR, group_id)
				
	def lighting_group_ramp(self, group_id, duration, level=1.0):
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
		if not (0.0 <= level <= 1.0):
			raise ValueError, 'Ramp level is out of bounds.  Must be between 0.0 and 1.0 (got %r).' % level
		
		if not (MIN_RAMP_RATE <= duration <= MAX_RAMP_RATE):
			raise ValueError, 'Duration is out of bounds, must be between %d and %d (got %r)' % (MIN_RAMP_RATE, MAX_RAMP_RATE, duration)
		
	def recall(self, unit_addr, param_no, count):
		"""
		Recalls a value from the unit.
		
		TODO: write documentation for this.
		"""
		
		pass
	
	def identify(self, unit_addr, attribute):
		"""
		TODO: write documentation for this.
		"""
		
		pass
		
		
