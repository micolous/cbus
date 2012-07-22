Applications
============

Running ontop of the C-Bus protocols are applications.

This package provides encoders and decoders for application-level messages on
the C-Bus network.

Application messages inside of C-Bus packets are called "Specific Application
Language", or SALs for short.  A packet may contain many SALs for a single
application, up to the MTU of the C-Bus network.


.. toctree::
	:maxdepth: 2
	
	cbus.protocol.application.lighting
	cbus.protocol.application.temperature

