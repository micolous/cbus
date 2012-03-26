# libcbus #

Talks to C-Bus using Python.

Currently only supports the [C-Bus Serial PC Interface (PCI), 5500PC](http://www2.clipsal.com/cis/technical/product_groups/cbus/system_units_and_accessories/pc_interface).  The USB version (5500PCU) is currently not supported.

Note that Clipsal say something about "voiding warranties" if you use non-Clipsal software to connect to your C-Bus network without prior authorisation.

## Hacking Notes ##

Official serial protocol documentation: http://training.clipsal.com/downloads/OpenCBus/OpenCBusProtocolDownloads.html

The C-Bus Toolkit software has a CNI (network) interface mode.  This is really just the serial protocol over a TCP socket.  Note that libcbus does not currently implement a CNI client.  There's a further discovery protocol, however this requires special implementation (that I'm not sure is worth it).

If you want to see how Toolkit interacts with a Serial PCI, use the `tcp_serial_redirect.py` script from the [pySerial example scripts](http://pyserial.sourceforge.net/examples.html#tcp-ip-serial-bridge).  This can be run even on a non-Windows machine, for dealing with pesky 100 different revisions of PL2303 USB-Serial adapters that require different and conflicting Windows drivers.  For example:

    $ python tcp_serial_redirect.py -p /dev/ttyUSB0 -P 22222
	
Congratulations, you now have turned your computer and a [5500PC](http://www2.clipsal.com/cis/technical/product_groups/cbus/system_units_and_accessories/pc_interface) into a [5500CN](http://www2.clipsal.com/cis/technical/product_groups/cbus/system_units_and_accessories/ethernet_interface) without writing a single line of custom code, and saved about 200$.  Even a [Beaglebone can be had for less than 200$](http://beagleboard.org/bone). ;)

Go into Toolkit, set the Default Interface type to "IP Address (CNI)" with the IP and port of the machine running the serial redirector.

You can then use tools like Wireshark to monitor interactions with the C-Bus PCI, instead of using kernel hacks to sniff serial, other redirects, or wireing up your own serial sniffer device.  This will aid if you wish to use undocumented commands, or isolate issues in the Clipsal documentation.

You could also use this with tools like C-Gate to get a higher level interface with the C-Bus PCI.
