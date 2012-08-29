# libcbus [![Build Status](https://secure.travis-ci.org/micolous/cbus.png?branch=master)](http://travis-ci.org/micolous/cbus) #

Talks to C-Bus using Python.

Copyright 2012 Michael Farrell.  Licensed under the GNU LGPL3+.  For more details see `COPYING` and `COPYING.LESSER`.

Clipsal state that use of C-Bus with non-Clipsal hardware or software may void your warranty.

Additional documentation for the project is published at http://cbus.rtfd.org/

## Hardware Interface Support ##

Currently only supports the [C-Bus Serial PC Interface (PCI), 5500PC](http://www2.clipsal.com/cis/technical/product_groups/cbus/system_units_and_accessories/pc_interface).  The USB version (5500PCU) may work if you have the appropriate `cp210x` kernel module, but it is untested.

This is a reimplementation of the PCI serial protocol from scratch.

It does **not** use the `libcbm` library/DLL from Clipsal, or C-Gate:

 * The `libcbm` module only runs on `x86_32` systems, and is only available as a static library (closed source).  
 * C-Gate requires an OS and architecture specific closed source serial library (SerialIO), the Java runtime, and itself has various licensing restrictions.

As such, it should run on any Python supported platform, with the exeception of `dbus` (IPC server) components which don't work properly on Windows. 

The software itself has been primarily developed on Linux with on armhf, x86_32 and x86_64 systems.

