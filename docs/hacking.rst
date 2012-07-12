*******
Hacking
*******

Information about using the hardware.

Official documentation
======================

Official serial protocol documentation is available from Clipsal's website: http://training.clipsal.com/downloads/OpenCBus/OpenCBusProtocolDownloads.html

At present, we support a subset of the "lighting" application only.

Comparison to ``libcbm``
========================

``libcbm`` supports to C-Bus protocol completely, including conforming to the various "protocol certification levels".  It is closed source and written in C, and only will work with ia32 Windows and Linux systems.  It is distributed for Linux as a static library in an RPM.

``libcbus`` supports only the lighting application (at present).  It is open source (LGPL3+) and written in Python, and will work with any Python supported platform.

``libcbus`` also includes an abstraction daemon called ``cdbusd`` which will allow multiple applications to simultaneously use the PCI.  This daemon requires D-Bus, which is not available on Windows.  Other components of ``libcbus`` will continue to function.

Comparison to C-Gate
====================

C-Gate is Clipsal's own C-Bus control software.  It is a closed source application written in Java, that uses the SerialIO library (also closed source) or sockets to communicate with a PCI.

Toolkit itself uses C-Gate in order to communicate with the PCI.  It supports a wide range of operations through it's own protocol, including reprogramming the network.

However, the SerialIO library included with C-Gate is only available on 32-bit platforms, and even then only on Windows and ancient versions of Linux.

CNI / network protocol
======================

The C-Bus Toolkit software has a CNI (network) interface mode.  This is really just the serial protocol over a TCP socket.  Note that libcbus does not currently implement a CNI client.  There's a further discovery protocol, however this requires special implementation which has not been done.

Setting up a fake CNI and sniffing the protocol
===============================================

If you want to see how Toolkit interacts with a Serial PCI, use the ``tcp_serial_redirect.py`` script from the 'pySerial example scripts`_.  This can be run even on a non-Windows machine, for dealing with pesky 100 different revisions of PL2303 USB-Serial adapters that require different and conflicting Windows drivers.  For example::

    $ python tcp_serial_redirect.py -p /dev/ttyUSB0 -P 22222
	
Congratulations, you now have turned your computer and a `5500PC`_ into a `5500CN`_ without writing a single line of custom code, and saved about 200$.  Even a `Beaglebone`_ can be had for less than 200$. ;)

Go into Toolkit, set the Default Interface type to "IP Address (CNI)" with the IP and port of the machine running the serial redirector.

You can then use tools like Wireshark to monitor interactions with the C-Bus PCI, instead of using kernel hacks to sniff serial, other redirects, or wireing up your own serial sniffer device.  This will aid if you wish to use undocumented commands, or isolate issues in the Clipsal documentation.

You could also use this with tools like C-Gate to get a higher level interface with the C-Bus PCI.

USB support / 5500PCU
=====================

Clipsal's driver is not digitally signed.

It appears to use the driver ``silabser.sys`` on Windows, which corresponds to a Silicon Labs CP210X USB-serial bridge.  ``cbususb.inf`` lists the following products:

* ``10C4:EA60``: Generic SiLabs CP210X
* ``166A:0101``: C-Bus Multi-room Audio Matrix Switcher (`560884`_)
* ``166A:0201``: C-Bus Pascal/Programmable Automation Controller (`5500PACA`_)
* ``166A:0301``: C-Bus Wireless PC Interface (5800PC).  This appears to be an unreleased product.
* ``166A:0303``: C-Bus Wired PC Interface (`5500PCU`_)
* ``166A:0304``: C-Bus Black & White Touchscreen Mk2 (`5000CT2`_)
* ``166A:0305``: C-Bus C-Touch Spectrum Colour Touchscreen (`C-5000CT2`_)
* ``166A:0401``: C-Bus Architectural Dimmer (L51xx series)

Of these, in Linux, only the generic adapter and `5500PCU`_ are supported by the ``cp210x`` kernel module.

.. _5500PC: http://www2.clipsal.com/cis/technical/product_groups/cbus/system_units_and_accessories/pc_interface
.. _5500PCU: http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=5500PCU&ref=
.. _5500CN: http://www2.clipsal.com/cis/technical/product_groups/cbus/system_units_and_accessories/ethernet_interface
.. _Beaglebone: http://beagleboard.org/bone
.. _pySerial example scripts: http://pyserial.sourceforge.net/examples.html#tcp-ip-serial-bridge
.. _560884: http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=560884/2&ref=
.. _5500PACA: http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=5500PACA&ref=
.. _5000CT2: http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=5000CT2WB&ref=
.. _C-5000CT2: http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=C-5000CTDL2&ref=
