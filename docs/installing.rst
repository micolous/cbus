******************
Installing libcbus
******************

.. highlight:: console

.. note::

	This section is incomplete.

All components (system install)
===============================

You need Python 3.7 or later installed.  You can build the software and its dependencies with::

    $ pip3 install -r requirements.txt
    $ python3 setup.py install

This will install everything, including :program:`cmqttd`.

C-Bus MQTT bridge only (Docker image)
=====================================

If you *only* want to use :doc:`the C-Bus MQTT bridge (cmqttd) <cmqttd>`, then you should use the
``Dockerfile`` included in this repository.

This uses a minimal `Alpine Linux`__ image as a base, and contains the *bare minimum* needed to
make :program:`cmqttd` work.

__ https://alpinelinux.org/

On a system with Docker installed, clone the `libcbus git repository`__ and then run::

    # docker build -t cmqttd .

__ https://github.com/micolous/cbus


This will download about 120 MiB of dependencies, and result in about 100 MiB image (named
``cmqttd``).

The image *always* uses the following environment variables:

* ``TZ``: The timezone to use when sending a time signal to the C-Bus network.

  This must be a `tz database timezone name`__ (eg: ``Australia/Adelaide``). The default (and
  fall-back) timezone is `UTC`__.

__ https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
__ https://en.wikipedia.org/wiki/Coordinated_Universal_Time

The *default* start-up script supports a serial or USB PCI, and will connect (*without* transport
security) to an *unauthenticated* MQTT Broker of your choice. Configure it with these environment
variables:

* ``SERIAL_PORT``: The serial port that the PCI is connected to. USB PCIs appear as a serial device
  (``/dev/ttyUSB0``). Docker _also_ requires the ``--device`` option so that it is forwarded into
  the container.

  This is equivalent to the ``-s`` (or ``--serial``) option to :program:`cmqttd`.

* ``MQTT_SERVER``: IP address where the MQTT Broker is running.

  This is equivalent to the ``-b`` (or ``--broker-address``) option to :program:`cmqttd`.

For example, to use a PCI on ``/dev/ttyUSB0``, with an MQTT Broker at ``192.0.2.1`` and the time
zone set to ``Australia/Adelaide``::

    # docker run --device /dev/ttyUSB0 -e "SERIAL_PORT=/dev/ttyUSB0" \
        -e "MQTT_SERVER=192.0.2.1" -e "TZ=Australia/Adelaide" cmqttd

If you want to run the daemon manually with other settings (eg: a CNI at ``192.0.2.2:10001``), you
can run ``cmqttd`` manually within the container (ie: skipping the start-up script) with::

    # docker run -e "TZ=Australia/Adelaide" cmqttd cmqttd \
        -b 192.0.2.1 -t 192.0.2.2:10001 --broker-disable-tls

.. note::

    When running without the start-up script, you must write ``cmqttd`` twice: first as the name of
    the image, and second as the name of the program inside the image to run.
	
If you want to run the ``cmqttd`` daemon on the same device as the Home Assistant server with the
MQTT broker add-on you can::

    # docker run -d --device /dev/ttyUSB0 --network hassio \
        -e "TZ=Australia/Adelaide" cmqttd cmqttd \
        -s /dev/ttyUSB0 -b 172.30.33.0 --broker-disable-tls

.. note::

    The IP address for the MQTT broker on the hassio docker network may be discovered with:
        # docker network inspect hassio

More information about options is available from :doc:`the cmqttd doc page <cmqttd>`.
