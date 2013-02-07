************
Introduction
************

Welcome to libcbus!

This is a Python library for interacting with Clipsal CBus units, and provides some additional utility functions, such as:

* A high-level DBus-based API for sharing a CBus PCI with multiple application on a computer.
* A library for parsing information from CBus Toolkit project backup files.
* A "fake PCI" test server for parsing data sent by CBus applications.

What is CBus?
=============

CBus is a home automation and electrical control system made by Clipsal.  It's also known as Square D in the United States, and sold under other brands worldwide by Schnider Electric.

It uses low voltage wiring for light switches (panels) and other sensors, and centrally-fed dimmer and relay controls for devices (such as lights).

CBus has a unit called the PCI (PC Interface) and the CNI (CBus Network Interface) which interactions with the CBus network via Serial and TCP/IPv4 respectively.  These use a common interface described by the Serial Interface Guide, and other public CBus specification documents.

The PCI also has a USB variant which includes a USB to Serial converter.

Clipsal's official interfaces
=============================

In addition to protocol documentation, Clipsal also provide two systems for interacting with CBus, ``libcbm`` and C-Gate.  Clipsal's own software (like Toolkit) and hardware (like Wiser) uses this to interact with CBus networks over serial and IPv4.

Comparison to ``libcbm``
------------------------

``libcbm`` supports to C-Bus protocol completely, including conforming to the various "protocol certification levels".  It is closed source and written in C, and only will work with ia32 Windows and Linux systems.  It is distributed for Linux as a static library in an RPM.

``libcbus`` supports only the lighting application (at present).  It is open source (LGPL3+) and written in Python, and will work with any Python supported platform.

``libcbus`` also includes an abstraction daemon called ``cdbusd`` which will allow multiple applications to simultaneously use the PCI.  This daemon requires D-Bus, which is not available on Windows.  Other components of ``libcbus`` will continue to function.

Comparison to C-Gate
--------------------

C-Gate is Clipsal's own C-Bus control software.  It is a closed source application written in Java, that uses the SerialIO library (also closed source) or sockets to communicate with a PCI.

Toolkit itself uses C-Gate in order to communicate with the PCI.  It supports a wide range of operations through it's own protocol, including reprogramming units on the network.

However, the SerialIO library included with C-Gate is only available on 32-bit platforms, and even then only on Windows and ancient versions of Linux.

So where does libcbus come in?
==============================

libcbus primarily provides three ways to communicate with C-Bus, with varying levels of complexity and abstraction:

* A low level API which allows direct encoding and decoding of packets.  It exposes parts of the packet as classes with attributes.
* A medium level API which handles access to the C-Bus PCI through the Twisted networking library and PySerial.  You can insert your own protocol handler, or work with the lower level API in order to access the library at a level that suits you.  There are both server (FakePCI) and client interfaces.
* A high level API which provides access to C-Bus over DBus.  This allows multiple applications on your computer to interact with the CBus network in a simple way, and allows you to use other DBus supporting languages (such as bash, C, C#, Perl, Python, Ruby, and Vala) to interact with the network through a single PCI.
 
libcbus does this using completely open source code (LGPLv3), and works across all Python supported platforms.  Platforms that don't support DBus (such as Windows) will be able to use the lower level APIs only, and lack the sharing functionality.

I've tested this primarily with Linux on armel, armhf, amd64 and i386, and Windows on amd64.
