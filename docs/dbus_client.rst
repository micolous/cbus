.. _dbus-client:

D-Bus Client API
================

The recommended way to interact with libcbus is through cdbusd and it's D-Bus API.

It allows many applications, written in any language with D-Bus bindings to interact with the network with one PCI.

This document describes the interface au.id.micolous.cbus.CBusInterface.

Included in this document is examples of syntax for use with mdbus2, a command-line D-Bus testing tool.  Types are given in D-Bus notation.


.. method:: lighting_group_on(group_addr)

	Turns on lights for the given group addresses.

	:param group_addr: Group addresses to turn on lights for, up to 9.
	:type group_addr: ay
	
	.. code-block:: sh

		# Turn on lights for GA 1 and 2.
		mdbus2 -s au.id.micolous.cbus.CBusService / au.id.micolous.cbus.CBusInterface.lighting_group_on '(1, 2)'

.. method:: lighting_group_off(group_addr)

	Turns off lights for the given group addresses.
	
	:param group_addr: Group addresses to turn off lights for, up to 9.
	:type group_addr: ay
		
	:returns: Single-byte string with code for the confirmation event.
	:rtype: string

	.. code-block:: sh

		# Turn off lights for GA 3 and 4.
		mdbus2 -s au.id.micolous.cbus.CBusService / au.id.micolous.cbus.CBusInterface.lighting_group_off '(3, 4)'

.. method:: lighting_group_ramp(group_addr, duration, level)

	Ramps (fades) a group address to a specified lighting level.

	Note: C-Bus only supports a limited number of fade durations, in decreasing
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

	.. code-block:: sh
	
		# Fades GA 5 to 45% brightness over 12 seconds.
		mdbus2 -s au.id.micolous.cbus.CBusService / au.id.micolous.cbus.CBusInterface.lighting_group_ramp 5 12 0.45
