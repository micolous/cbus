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


Installing
==========

.. highlight:: console

.. note::

	This section is incomplete.

All components
--------------

You need Python 3.7 or later installed.  You can build the software and its dependencies with::

    $ pip3 install -r requirements.txt
    $ python3 setup.py install

C-Bus MQTT bridge (``cmqttd``)
------------------------------

If you just want to use :doc:`the C-Bus MQTT bridge (cmqttd) <daemons.cmqttd>`, then you should
use the ``Dockerfile`` included in this repository.

This uses a minimal `Alpine Linux`__ image as a base, and contains the bare minimum needed to make
``cmqttd`` work.

__ https://alpinelinux.org/

On a system with Docker installed, clone the ``libcbus`` repository and then run::

    # docker build -t cmqttd .

This will download about 120 MiB of dependencies, and result in about 100 MiB image.

The __default__ start-up script supports a serial or USB PCI, and will connect to unauthenticated
MQTT Brokers without transport security.

The image uses the following environment variables:

* ``TZ``: The timezone to use when sending a time signal to the C-Bus network.

  This must be a `tz database timezone name`__ (eg: ``Australia/Adelaide``).

  This environment variable is __always__ used. The default timezone is `UTC`__.

* ``SERIAL_PORT``: The serial port that the PCI is connected to. USB PCIs appear as a serial device
  (``/dev/ttyUSB0``). Also requires the ``--device`` option so Docker forwards the device into the
  container.

  This environment variable is __only__ used by the default start-up script.

* ``MQTT_SERVER``: IP address where the MQTT Broker is running.

  This environment variable is __only__ used by the default start-up script.

__ https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
__ https://en.wikipedia.org/wiki/Coordinated_Universal_Time

For example, to use a PCI on ``/dev/ttyUSB0``, with an MQTT Broker at ``192.0.2.1`` and the time
zone set to ``Australia/Adelaide``::

    # docker run --device /dev/ttyUSB0 -e "SERIAL_PORT=/dev/ttyUSB0" \
        -e "MQTT_SERVER=192.0.2.1" -e "TZ=Australia/Adelaide" cmqttd

If you want to run the daemon manually with other settings (eg: a CNI at ``192.0.2.2:10001``), you
can do so with::

    # docker run -e "TZ=Australia/Adelaide" cmqttd cmqttd \
      -b 192.0.2.1 -t 192.0.2.2:10001 --broker-disable-tls

More information about options is available from :doc:`the cmqttd doc page <daemons.cmqttd>`.
