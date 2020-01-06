# libcbus

[![Build Status](https://secure.travis-ci.org/micolous/cbus.png?branch=master)][travis]
[![Coverage Status](https://coveralls.io/repos/github/micolous/cbus/badge.svg)][coveralls]

Talks to Clipsal C-Bus using Python.

Copyright 2012-2019 Michael Farrell. Licensed under the GNU LGPL3+. For more
details see `COPYING` and `COPYING.LESSER`.

**Note:** This software is not certified or endorsed by Clipsal or Schneider
Electric. Clipsal claim that use of C-Bus with non-Clipsal hardware or
software may void your warranty.

More information about the project is available on
[the libcbus ReadTheDocs site][rtd], and in the `docs` directory of the source
repository.

## Hardware interface support

This should work with the following C-Bus PC Interfaces (PCIs):

* [5500PC Serial PCI][5500PC]

* [5500PCU USB PCI][5500PCU]

  On Linux, this requires v2.6.25 or later kernel, with the `cp210x` module.

* [5500CN Ethernet PCI][5500CN] (and likely _also_ [5500CN2][])

  This software _does not_ support configuring the Ethernet PCI for the first
  time. It must already have an IP address on your network.

## About this project

This is a reimplementation of the PCI serial protocol _from scratch_.

It does **not** use the `libcbm` library/DLL from Clipsal, or C-Gate:

* The `libcbm` module only runs on `x86_32` systems, and is only available
  as a static library (closed source).

* C-Gate requires an OS and architecture specific closed source serial
  library (SerialIO), the Java runtime, and itself has various licensing
  restrictions.

As such, it should run on any Python supported platform, with the exception
of `dbus` (IPC server) components which don't work properly on Windows.

The software itself has been primarily developed on Linux with on armhf,
x86_32 and x86_64 systems.

The most useful bits of this project are:

* `cdbusd`, which shares events from the C-Bus PCI in D-Bus.

* `cmqttd`, which bridges a C-Bus PCI to an MQTT Broker (for use with Home Assistant).

[rtd]: https://cbus.rtfd.org/
[coveralls]: https://coveralls.io/github/micolous/cbus
[travis]: https://travis-ci.org/micolous/cbus
[5500PC]: https://www.clipsal.com/Trade/Products/ProductDetail?catno=5500PC
[5500PCU]: https://www.clipsal.com/Trade/Products/ProductDetail?catno=5500PCU
[5500CN]: https://updates.clipsal.com/ClipsalOnline/Files/Brochures/W0000348.pdf
[5500CN2]: https://www.clipsal.com/Trade/Products/ProductDetail?catno=5500CN2
