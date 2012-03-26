#!/usr/bin/env python
"""
Library to give extra features to SafeConfigParser.
Copyright 2011 Michael Farrell <http://micolous.id.au/>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

try:
	# py3
	from configparser import SafeConfigParser, NoOptionError
except ImportError:
	# py2
	from ConfigParser import SafeConfigParser, NoOptionError

class ConfigParserPlus(SafeConfigParser):
	"""
ConfigParserPlus changes the behaviour of the SafeConfigParser constructor so it takes in a two-dimensional dict of defaults (which is much simpler to handle).  You could also pass it something that implements a 2D dict.

has_option performs identically to the underlying SafeConfigParser -- if an option is not in the configuration, it will return False (even if a default is available).

Default values will be cast for getint and getfloat, unless the default value is None.  get and getfloat will not cast values.
	"""

	def __init__(self, defaults, allow_no_value=False):
		SafeConfigParser.__init__(self)
		# apparently self._defaults is used by the default implementation.
		self._cfp_defaults = defaults
		self._allow_no_value = allow_no_value

	def defaults(self):
		"""Return the 2D dict that is providing defaults.."""
		return self._cfp_defaults

	def _get_with_default(self, section, option, method, coercion=None):
		try:
			return getattr(SafeConfigParser, method)(self, section, option)
		except NoOptionError:
			try:
				v = self._cfp_defaults[section][option]
			except KeyError, ex:
				if self._allow_no_value:
					return None
				else:
					raise ex
			else:
				if coercion != None and v != None:
					v = coercion(v)
				return v

	def get(self, section, option):
		return self._get_with_default(section, option, 'get')

	def getint(self, section, option):
		return self._get_with_default(section, option, 'getint', int)

	def getboolean(self, section, option):
		return self._get_with_default(section, option, 'getboolean')

	def getfloat(self, section, option):
		return self._get_with_default(section, option, 'getfloat', float)

