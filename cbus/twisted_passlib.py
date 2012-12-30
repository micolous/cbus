#!/usr/bin/env python
# twisted_passlib.py - ICredentialsChecker interface for passlib.apache.HtpasswdFile
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


from passlib.apache import HtpasswdFile
from zope.interface import implements, Interface
from twisted.internet import defer
from twisted.python import failure, log
from twisted.cred import error, credentials
from twisted.cred.checkers import ICredentialsChecker



class ApachePasswordDB(object):
	"""
	Very simple glue between passlib.apache.HtpasswdFile to make it an
	ICredentialsChecker in Twisted.
	
	"""
	implements(ICredentialsChecker)

	# we can only implement non-hashing functions as the passwords
	# may be hashed.
	credentialInterfaces = (
		credentials.IUsernamePassword,
	)

	def __init__(self, filename):
		self._ht = HtpasswdFile(filename)
	
	def requestAvatarId(self, c):
		if self._ht.check_password(c.username, c.password):
			# success, return username
			return defer.succeed(c.username)
		else:
			# bad credentials
			return defer.fail(error.UnauthorizedLogin())
			
	
