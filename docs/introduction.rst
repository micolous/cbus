************
Introduction
************

Welcome to ``libcbus``!

This is a Python library for interacting with Clipsal C-Bus networks through a
:abbr:`PCI (PC Interface)` or :abbr:`CNI (C-Bus Network Interface)`.

This consists of:

* :doc:`A C-Bus MQTT bridge (cmqttd) <cmqttd>`, which provides a high level API for controlling
  C-Bus networks with other systems (such as Home Assistant)

* A low-level interface for parsing and producing C-Bus packets, and using a PCI with
  :py:mod:`asyncio`

* A library for parsing information from C-Bus Toolkit project backup files, and visualising
  networks with :program:`graphviz`

* A "fake PCI" test server for parsing data sent by C-Bus applications.

It is a completely open source implementation (LGPLv3) of the C-Bus PCI/CNI protocol in Python,
based on `Clipsal's public documentation of the PCI Serial Interface`__ and some reverse
engineering.

__ https://updates.clipsal.com/ClipsalSoftwareDownload/DL/downloads/OpenCBus/OpenCBusProtocolDownloads.html

Unlike a number of other similar projects, it _does_ _not_ depend on
:ref:`C-Gate or libcbm <clipsal-other-interfaces>`. This makes the code much more portable between
platforms, as well as avoiding the hazards of closed-source software. :)

.. warning::

    Despite using RJ45 connectors and CAT-5 cabling commonly associated with Ethernet networks,
    C-Bus uses totally different signalling (about 10 kbit/s) and has a 36 volt power feed.

    _You cannot patch an ordinary network card into a C-Bus network._

    This project *requires* a :abbr:`PCI (PC Interface)` or :abbr:`CNI (C-Bus Network Interface)` to
    communicate with a C-Bus network.

What is C-Bus?
==============

C-Bus is a home automation and electrical control system made by Clipsal. It's also known as Square
D in the United States, and sold under other brands worldwide by Schnider Electric.

It uses low voltage (36 volts) wiring for light switches (panels) and other sensors, and
centrally-fed dimmer and relay controls for devices (such as lights).

The C-Bus :abbr:`PCI (PC Interface)` and :abbr:`CNI (C-Bus Network Interface)` can interface with
a C-Bus network via Serial [#f1]_ and TCP/IPv4 respectively. These use a common interface described
in the `Serial Interface Guide`__, and `other public C-Bus documentation`__.

__ https://updates.clipsal.com/ClipsalSoftwareDownload/DL/downloads/OpenCBus/Serial%20Interface%20User%20Guide.pdf
__ https://updates.clipsal.com/ClipsalSoftwareDownload/DL/downloads/OpenCBus/OpenCBusProtocolDownloads.html

.. [#f1] The PCI is also available in a USB variant, which uses an in-built ``cp210x`` USB to
   Serial converter.  It is otherwise functionally identical to the Serial version.

.. _clipsal-other-interfaces:

Clipsal's other interfaces
==========================

In addition to protocol documentation, Clipsal also provide two systems for interacting with C-Bus,
``libcbm`` and C-Gate. Clipsal's own software (like Toolkit) and hardware (like Wiser) use this to
interact with C-Bus networks over serial and IPv4.

``libcbm``
----------

``libcbm`` supports to C-Bus protocol completely, including conforming to the various "protocol
certification levels".

It is closed source and written in C, and only will work with ia32 Windows and Linux systems. It is
distributed for Linux as a static library in an RPM.

C-Gate
------

C-Gate is a closed source, C-Bus abstraction service written in Java.

It appears to support a subset of the C-Bus protocol, and comparing its interactions with a PCI with
the Serial Interface Guide seems to suggest it is using a bunch of commands that are officially
deprecated.

It depends on the (closed source) SerialIO library for serial communication, which requires a
:abbr:`JNI (Java Native Interface)` library that is only available on ``ia32`` Windows and old
versions of Linux.
