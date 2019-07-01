*******
Hacking
*******

Information about using the hardware and software.

Official documentation
======================

You should implement software in conjunction with reading `the official
documentation`_. This library attempts to follow its terminology and
structures, so understanding what is happening on a lower level is needed
particularly when using the lower level interfaces in this library.

There is a large amount of documentation in there that says "these items are
deprecated and shouldn't be used". I've noticed that C-Gate and Toolkit will
interact with the hardware in these "deprecated" ways...

This doesn't mean implement the library to talk this way. You should implement
it properly. Just be aware than when working with implementing a fake PCI or
parsing out packets that Clipsal's software generated, be aware they'll do
strange and undocumented things.

Geoffry Bennett's reverse engineering notes (2001 - 2004)
---------------------------------------------------------

Geoffry Bennett gave a talk at a `LinuxSA meeting in 2001`_ and at
`Linux.conf.au 2004`_ about his experiences with reverse engineering C-Bus.
At the time there was no official protocol documentation available.

The `Linux.conf.au 2004`_ notes cover a lot more information, includes some
information about dumping and reverse engineering the contents of NVRAM in
units, a Perl client library, and an emulator used for older versions of the
Clipsal programming software.

CNI / network protocol
======================

The C-Bus Toolkit software has a CNI (network) interface mode, which is just
the serial protocol over a TCP socket.

Some of the tools here support running in TCP mode with ``-t``.

There's also a discovery protocol, however this has not been implemented yet.
Patches welcome. :)

Setting up a fake CNI and sniffing the protocol
===============================================

If you want to see how Toolkit interacts with a Serial PCI, use the
``tcp_serial_redirect.py`` script from the `pySerial example scripts`_.

For example::

    $ python tcp_serial_redirect.py -p /dev/ttyUSB0 -P 22222
	
Congratulations, you now have turned your computer and a `5500PC`_ into a
`5500CN`_ without writing a single line of custom code, and saved about 200$.
Even a `Beaglebone`_ can be had for less than 200$. ;)

Go into Toolkit, set the Default Interface type to "IP Address (CNI)" with the
IP and port of the machine running the serial redirector.

You can then use tools like `Wireshark`_ to monitor interactions with the
C-Bus PCI, instead of using kernel hacks to sniff serial, other redirects, or
wiring up your own serial sniffer device. This will aid if you wish to use
undocumented commands, or isolate issues in the Clipsal documentation.

You could also use this with tools like C-Gate to get a higher level interface
with the C-Bus PCI.

USB support / 5500PCU
=====================

Clipsal's driver is not digitally signed.

It uses ``silabser.sys`` on Windows, which corresponds to a Silicon Labs
CP210X USB-serial bridge. ``cbususb.inf`` lists the following products:

* ``10C4:EA60``: Generic SiLabs CP210X
* ``166A:0101``: C-Bus Multi-room Audio Matrix Switcher (`560884`_)
* ``166A:0201``: C-Bus Pascal/Programmable Automation Controller
  (`5500PACA`_)
* ``166A:0301``: C-Bus Wireless PC Interface (5800PC). This appears to be an
  unreleased product.
* ``166A:0303``: C-Bus Wired PC Interface (`5500PCU`_)
* ``166A:0304``: C-Bus Black & White Touchscreen Mk2 (`5000CT2`_)
* ``166A:0305``: C-Bus C-Touch Spectrum Colour Touchscreen
  (`C-5000CT2`_)
* ``166A:0401``: C-Bus Architectural Dimmer (L51xx series)

Linux kernel module
-------------------

The ``cp210x`` kernel module in Linux 2.6.30 and later supports this chipset.
However, only the generic adapter and `5500PCU`_ device IDs are included with
the kernel for versions before 3.2.22 and 3.5-rc6.

Your distribution vendor may backport the patches in to other kernel versions.

To see which devices your kernel supports, run the following command::

	$ /sbin/modinfo cp210x | grep v166A

If the following is returned, you only have support for the `5500PCU`_::

	alias:          usb:v166Ap0303d*dc*dsc*dp*ic*isc*ip*

If more lines come back, then your kernel supports all the hardware that is
known about at this time.

Unit Tests
==========

There's some basic unit tests that are written that require you have the
``nosetests`` package (``nose`` on pip).

When you run ``nosetests``, it will discover all the unit tests in the package
and try to run them.

I'm targeting Python 2.6 and 2.7 at this time. Python 3 support is currently a
work in progress.  Patches still welcome.

When implementing a new application, you should copy all of the examples given
in the documentation of that application into some tests for that application.
Be careful though, there are sometimes errors in Clipsal's documentation, so
double check to make sure that the examples are correct. If you find errors in
Clipsal's documentation, you should email them about it.

.. _the official documentation: https://updates.clipsal.com/ClipsalSoftwareDownload/DL/downloads/OpenCBus/OpenCBusProtocolDownloads.html
.. _5500PC: https://www.clipsal.com/Trade/Products/ProductDetail?catno=5500PC
.. _5500PCU: https://www.clipsal.com/Trade/Products/ProductDetail?catno=5500PCU
.. _5500CN: https://updates.clipsal.com/ClipsalOnline/Files/Brochures/W0000348.pdf
.. _5500CN2: https://www.clipsal.com/Trade/Products/ProductDetail?catno=5500CN2
.. _Beaglebone: http://beagleboard.org/bone
.. _pySerial example scripts: http://pyserial.sourceforge.net/examples.html#tcp-ip-serial-bridge
.. _560884: http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=560884/2&ref=
.. _5500PACA: http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=5500PACA&ref=
.. _5000CT2: http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=5000CT2WB&ref=
.. _C-5000CT2: http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=C-5000CTDL2&ref=
.. _Wireshark: http://www.wireshark.org/
.. _LinuxSA meeting in 2001: http://www.linuxsa.org.au/meetings/cbus.txt
.. _Linux.conf.au 2004: ftp://mirror.linux.org.au/pub/linux.conf.au/2004/papers/cbus/
