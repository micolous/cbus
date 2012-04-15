# libcbus #

Talks to C-Bus using Python.

Currently only supports the [C-Bus Serial PC Interface (PCI), 5500PC](http://www2.clipsal.com/cis/technical/product_groups/cbus/system_units_and_accessories/pc_interface).  The USB version (5500PCU) may work if you have the appropriate `cp210x` kernel module, but it is untested.

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

## Scripts ##

### `scripts/cdbusd.py` ###

Provides a DBus interface to CBus.  Requires dbus bindings for Python, which don't work on Windows.

### `scripts/cbusbot.py` ###

Provides an IRC interface to CBus.  Requires (my version of ircasync)[https://github.com/micolous/ircbots].

## USB Driver ##

(Note, this section is purely speculation!)

Clipsal's driver is not digitally signed.  It appears to use the driver `silabser.sys` on Windows, which corresponds to a Silicon Labs CP210X USB-serial bridge.  The INF file lists the following products:

* `10C4:EA60`: Generic SiLabs CP210X
* `166A:0101`: [C-Bus Multi-room Audio Matrix Switcher (560884)](http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=560884/2&ref=)
* `166A:0201`: [C-Bus Pascal/Programmable Automation Controller (5500PACA)](http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=5500PACA&ref=)
* `166A:0301`: C-Bus Wireless PC Interface (5800PC) This appears to be an unreleased product.
* `166A:0303`: [C-Bus Wired PC Interface (5500PCU)](http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=5500PCU&ref=)
* `166A:0304`: [C-Bus Black & White Touchscreen Mk2 (5000CT2)](http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=5000CT2WB&ref=)
* `166A:0305`: [C-Bus C-Touch Spectrum Colour Touchscreen (C-5000CT2)](http://updates.clipsal.com/ClipsalOnline/ProductInformation.aspx?CatNo=C-5000CTDL2&ref=)
* `166A:0401`: C-Bus Architectural Dimmer (L51xx series)

Supposedly this is supported in linux with the `cp210x` module, though I haven't tried this out.
