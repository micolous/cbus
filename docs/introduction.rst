************
Introduction
************

Welcome to ``libcbus``!

This is a Python library for interacting with Clipsal C-Bus networks through a
:abbr:`PCI (PC Interface)` or :abbr:`CNI (C-Bus Network Interface)`. This also includes:

* :doc:`A C-Bus MQTT bridge (cmqttd) <daemons.cmqttd>`, which provides a high level API for
  controlling C-Bus networks with other systems (such as Home Assistant)

* A low-level interface for parsing and producing C-Bus packets

* A library for parsing information from C-Bus Toolkit project backup files, and visualising
  networks with :program:`graphviz`

* A "fake PCI" test server for parsing data sent by C-Bus applications.

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

Clipsal's official interfaces
=============================

In addition to protocol documentation, Clipsal also provide two systems for interacting with C-Bus,
``libcbm`` and C-Gate. Clipsal's own software (like Toolkit) and hardware (like Wiser) use this to
interact with C-Bus networks over serial and IPv4.

Comparison to ``libcbm``
------------------------

``libcbm`` supports to C-Bus protocol completely, including conforming to the various "protocol
certification levels". It is closed source and written in C, and only will work with ia32 Windows
and Linux systems. It is distributed for Linux as a static library in an RPM.

``libcbus`` supports only the lighting application (at present).  It is open source (LGPL3+) and
written in Python, and will work with any Python supported platform.

``libcbus`` also includes abstraction tools that allow multiple applications to simultaneously use
the PCI.

Comparison to C-Gate
--------------------

C-Gate is Clipsal's own C-Bus control software. It is a closed source application written in Java,
that uses the SerialIO library (also closed source) or sockets to communicate with a PCI.

Toolkit itself uses C-Gate in order to communicate with the PCI. It supports a wide range of
operations through it's own protocol, including reprogramming units on the network.

However, the SerialIO library included with C-Gate is only available on 32-bit platforms, and even
then only on Windows and ancient versions of Linux.

So where does libcbus come in?
==============================

``libcbus`` primarily provides three ways to communicate with C-Bus, with varying levels of
complexity and abstraction:

* A low-level API which allows direct encoding and decoding of packets. It exposes parts of the
  packet as classes with attributes.

* A medium-level API which handles access to the C-Bus PCI through ``asyncio`` and PySerial. You
  can insert your own protocol handler, or work with the lower level API in order to access the
  library at a level that suits you. There are both server (FakePCI) and client interfaces.

* A high level API which provides access to C-Bus over MQTT. This allows anything that can talk to
  MQTT to interact with the network using a single PCI.
 
``libcbus`` does this using completely open source code (LGPLv3), and works across all Python
supported platforms.

I've tested this primarily with Linux on armel, armhf, amd64 and i386, and macOS on amd64.
