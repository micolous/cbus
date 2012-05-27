#!/usr/bin/env python
# staged: "simple" daemon for creating custom scenes listening on lighting GAs
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

"""
`staged` allows you to create simple scenes using INI files that listen for
lighting group address messages and transmits additional messages via cdbusd.

"""

DEFAULT_CONFIG_FILE = '/etc/cbus/staged.ini'
DEFAULT_CONFIG = {'staged': {}}
RESERVED_SECTIONS = ('staged', )
TRIGGER_RESERVED_KEYS = ('label', 'ga')

from configparser_plus import ConfigParserPlus
import dbus
import gobject
import sys
from optparse import OptionParser
from dbus.mainloop.glib import DBusGMainLoop
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
from cbus.daemon.cdbusd import DBUS_INTERFACE, DBUS_SERVICE, DBUS_PATH
import cbus.common
from twisted.python import log

class StagedEventHandler(object):
	def __init__(self, config, section, api):
		
		self.api = api
		self.label = config.get(section, 'label')
	
		# find all the GA triggers
		self.triggers = []
		
		for t in config.get(section, 'ga').split(','):
			t = t.strip()
			r = t.split(':')
			ga, state = int(r[0].strip()), r[1].strip().lower()
			
			if not cbus.common.validate_ga(ga):
				raise ValueError, 'Group address for trigger %r (%r) in group %r is invalid' % (t, ga, section)
				
			if state not in ('on', 'off'):
				raise ValueError, 'State for trigger %r (%r) in group %r is not "on" or "off"' % (t, state, section)

			self.triggers.append((ga, state))
		
		# now find all the actions to perform
		self.actions = []
		for ga, action in config.items(section):
			if ga not in TRIGGER_RESERVED_KEYS:
				ga, action = int(ga.strip()), action.lower().strip().split(':')
				
				if not cbus.common.validate_ga(ga):
					raise ValueError, 'Group address for action %r = %r in group %r is not valid' % (ga, action, section)
				
				if action[0] not in ('on', 'off', 'ramp'):
					raise ValueError, 'State for action %r = %r in group %r is not "on" or "off"' % (ga, action, section)
				
				if action[0] == 'ramp':
					# validate the ramping
					
					# convert percentage to fraction, clamp
					action[1] = float(action[1]) / 100.
					
					if action[1] < 0.:
						action[1] = 0.
						
					if action[1] > 1.:
						action[1] = 1.
					
					# clamp ramp rate
					action[2] = int(action[2])
					
					if action[2] < cbus.common.MIN_RAMP_RATE:
						action[2] = cbus.common.MIN_RAMP_RATE
					
					if action[2] > cbus.common.MAX_RAMP_RATE:
						action[2] = cbus.common.MAX_RAMP_RATE
					
					# remove unused parameters
					action = action[:3]
				else:
					# no other action commands take parameters
					action = [action[0]]
				
				self.actions.append((ga, action))
				
				
	
	def trigger(self):
		for ga, action in self.actions:
			print "trigger: %r, %r" % (ga, action)
			if action[0] == 'on':
				self.api.lighting_group_on(ga)
			elif action[0] == 'off':
				self.api.lighting_group_off(ga)
			elif action[0] == 'ramp':
				self.api.lighting_group_ramp(ga, action[2], action[1])
		

class Staged(object):
	
	triggers = {}
	
	def __init__(self, config, bus):
		obj = bus.get_object(DBUS_SERVICE, DBUS_PATH)
		api = dbus.Interface(obj, DBUS_INTERFACE)
		
		# parse config
		for section in config.sections():
			if section not in RESERVED_SECTIONS:
				# this is an event configuration.
				# parse it.
				eh = StagedEventHandler(config, section, api)
				
				# add to event handlers list
				for trigger in eh.triggers:
					if trigger not in self.triggers:
						self.triggers[trigger] = []
					
					self.triggers[trigger].append(eh)
				
		
		# vire event listeners
		for n, m in (
			('on_lighting_group_on', self.on_lighting_group_on),
			('on_lighting_group_off', self.on_lighting_group_off),
		):
			bus.add_signal_receiver(
				m,
				dbus_interface=DBUS_INTERFACE,
				bus_name=DBUS_SERVICE,
				path=DBUS_PATH,
				signal_name=n
			)
		

	

	def on_lighting_group_on(self, source_addr, group_addr):
		print "on_lighting_group_on: %r, %r" % (source_addr, group_addr)
		
		# look for triggers
		t = (group_addr, 'on')
		
		if t in self.triggers:
			[h.trigger() for h in self.triggers[t]]
		

	def on_lighting_group_off(self, source_addr, group_addr):
		print "on_lighting_group_off: %r, %r" % (source_addr, group_addr)
		
		# look for triggers
		t = (group_addr, 'off')
		
		if t in self.triggers:
			[h.trigger() for h in self.triggers[t]]


def boot(daemon_enable, pid_file, session_bus=False, settings_file=DEFAULT_CONFIG_FILE):
	if daemon_enable:
		raise ValueError, "daemon mode not supported yet"
	
	config = ConfigParserPlus(DEFAULT_CONFIG)
	
	if not config.read(settings_file):
		print "cannot read settings file %r" % settings_file
		sys.exit(1)
	
	if session_bus:
		bus = dbus.SessionBus()
	else:
		bus = dbus.SystemBus()
	
	staged = Staged(config, bus)
	
	loop = gobject.MainLoop()
	loop.run()


def main():
	parser = OptionParser(usage='%prog <staged.ini>')
	parser.add_option('-D', '--daemon',  action='store_true', dest='daemon', default=False, help='Start as a daemon [default: %default]')
	parser.add_option('-P', '--pid', dest='pid_file', default='/var/run/cdbusd.pid', help='Location to write the PID file.  Only has effect in daemon mode.  [default: %default]')
	parser.add_option('-S', '--session-bus', action='store_true', dest='session_bus', default=False, help='Bind to the session bus instead of the system bus [default: %default]')
	parser.add_option('-l', '--log-file', dest='log', default=None, help='Destination to write logs [default: stdout]')
	
	options, args = parser.parse_args()
	
	if options.log:
		log.startLogging(option.log)
	else:
		log.startLogging(sys.stdout)
	
	a = [options.daemon, options.pid_file, options.session_bus]
	
	if len(args) == 1:
		a.append(args[0])
	
	boot(*a)

if __name__ == '__main__':
	main()

	
	
