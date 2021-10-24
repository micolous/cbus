******
cmqttd
******

.. program:: cmqttd

.. highlight:: console

:program:`cmqttd` allows you to expose a C-Bus network to an MQTT broker. This daemon replaces
:program:`cdbusd` (which required D-Bus) as the abstraction mechanism for all other components.

It uses `Home Assistant`__ style `MQTT-JSON Light components`__, and supports `MQTT discovery`__.
It should also work with other software that supports MQTT.

__ https://www.home-assistant.io/
__ https://www.home-assistant.io/integrations/light.mqtt/#json-schema
__ https://www.home-assistant.io/docs/mqtt/discovery/

It :ref:`can also be run inside a Docker container <cmqttd-docker>`.

This replaces :program:`sage` (our custom web interface which replaced
:doc:`Wiser <wiser-swf-protocol>`).

:program:`cmqttd` with Home Assistant has many advantages over :doc:`Wiser <wiser-swf-protocol>`:

- No dependency on Flash Player or a mobile app
- No requirement for an Ethernet-based PCI (serial or USB are sufficient)
- Touch-friendly UI based on Material components
- Integrates with other Home Assistant supported devices
- No :ref:`hard coded back-doors <wiser-backdoor>` or outdated software from
  2006

See also: :ref:`Instructions for Wiser users <cmqttd-wiser>`.

.. note:: Only the default lighting application is supported by :program:`cmqttd`. Patches welcome!

Running
=======

:program:`cmqttd` requires a MQTT Broker (server) to act as a message bus.

.. note::

    For these examples, we'll assume your MQTT Broker:

    - is accessible via ``192.0.2.1`` on the default port (1883).
    - does not use transport security (TLS)
    - does not require authentication

    This setup is *not* secure; but securing your MQTT Broker is out of the scope of this document.

    For more information, see :ref:`mqtt-options`.

To connect to a serial or USB PCI connected on :file:`/dev/ttyUSB0`, run::

    $ cmqttd --broker-address 192.0.2.1 --broker-disable-tls --serial /dev/ttyUSB0

To connect to a CNI (or PCI over TCP) listening at ``192.0.2.2:10001``, run::

    $ cmqttd --broker-address 192.0.2.1 --broker-disable-tls --tcp 192.0.2.2:10001

If you're using Docker, the container also needs a route to the CNI's IP address.

.. tip::

    If you haven't :doc:`installed the library <installing>`, you can run from a ``git clone`` of
    ``libcbus`` source repository with::

        $ python3 -m cbus.daemons.cmqttd -b 192.0.2.1 [...]

.. _cmqttd-wiser:

For Wiser users
---------------

This software is **not** compatible with Wiser Home Control (Clipsal's web
interface for C-Bus). Wiser and :program:`cmqttd` both take full control the
CNI, and will interfere with one another.

Additionally, using both on the same C-Bus network (with different PCI/CNIs)
may cause issues, as both presume they are the sole source of network services
such as time synchronisation.

Wiser Home Control Mk1 (5200PG)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Wiser Home Control Mk1 has an external CNI which should be usable with
:program:`cmqttd`.

1. Switch off and completely disconnect the Wiser.

2. Disconnect the "busbar" between the Wiser and the CNI.

3. Connect the CNI to power and network directly.

   You may need to use Toolkit to configure the CNI with an IP address which
   can be accessed from the host you're running :program:`cmqttd` on. The
   default IP address for the CNI is ``192.168.2.2``.

4. Continue setting up :program:`cmqttd`.

5. Once you've verified :program:`cmqttd` is working correctly, responsibly
   dispose of the Wiser 1 at your nearest e-waste facility.

.. warning::

    The Wiser 1 has very outdated and insecure software (from 2006). *You
    should not use it under any circumstances, or for any purpose.*

Wiser Home Control Mk2 (5200WHC2)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Wiser Home Control Mk2 has an internal CNI which cannot be used,
because the Wiser's software conflicts with :program:`cmqttd`.

*You will need to get a real, standalone PCI or CNI.*

.. tip::

    The author of this software does not have access to any Wiser hardware
    anymore, and the Wiser 2's list price of 2000 AUD is far beyond the budget
    for this project.

    *Hint hint, Schneider Electric... we should talk :)*

.. _cmqttd-options:

Configuration
=============

:program:`cmqttd` has many command-line configuration options.

A complete list can be found by running ``cmqttd --help``.

C-Bus PCI options
-----------------

One of these *must* be specified:

.. option:: --serial DEVICE

    Serial device that the PCI is connected to, eg: ``/dev/ttyUSB0``.

    USB PCIs (5500PCU) act as a SiLabs ``cp210x`` USB-Serial adapter, its serial device must be
    specified here.

.. option:: --tcp ADDR:PORT

    IP address and TCP port where the PCI or CNI is located, eg: ``192.0.2.1:10001``.

    Both the address and the port are required. CNIs listen on port ``10001`` by default.

    See also: :ref:`Instructions for Wiser users <cmqttd-wiser>`.

.. _mqtt-options:

MQTT options
------------

.. option:: --broker-address ADDR

    Address of the MQTT broker. This option is required.

.. option:: --broker-port PORT

    Port of the MQTT broker.

    By default, this is 8883 if TLS is enabled, otherwise 1883.

.. option:: --broker-disable-tls

    Disables all transport security (TLS). This option is insecure!

    By default, transport security is enabled.

.. option:: --broker-auth FILE

    File containing the username and password to authenticate to the MQTT broker with.

    This is a plain text file with two lines: the username, followed by the password.

    If not specified, password authentication will not be used.

.. option:: --broker-ca DIRECTORY

    Path to a directory of CA certificates to trust, used for validating certificates presented in
    the TLS handshake.

    If not specified, the default (Python) CA store is used instead.

.. option:: --broker-client-cert PEM

.. option:: --broker-client-key PEM

    Path to a PEM-encoded client (public) certificate and (private) key for TLS authentication.

    If not specified, certificate-based client authentication will not be used.

    If the file is encrypted, Python will prompt for the password at the command-line.

Labels
------

.. option:: --project-file CBZ

    Path to a C-Bus Toolkit project backup file (CBZ) to use for labelling group addresses.

    This doesn't affect the entity paths or unique IDs published in MQTT.

    Only single-network projects using the lighting application are supported. DLT labels are not
    supported.

    For group addresses with unknown names, or if no project file is supplied, generated names like
    ``C-Bus Light 001`` will be used instead.

.. tip::

    If you don't have a project file backup from your installer, you can always rename entities
    from within Home Assistant itself.

    This labels are not stored on C-Bus units, so Toolkit cannot download this information from the
    network.

Time synchronisation
--------------------

By default, :program:`cmqttd` will periodically provide a time signal to the C-Bus network, and
respond to all time requests.

Local time is always used for time synchronisation. You can specify a different timezone with
`the TZ environment variable`__.

__ https://www.gnu.org/software/libc/manual/html_node/TZ-Variable.html

C-Bus' time implementation has many limitations:

* C-Bus date values and time values are two separate network variables – there is no analog to
  Python's ``datetime.datetime`` type.  This can trigger race conditions around midnight if the
  messages are not handled atomically by receivers.

  :program:`cmqttd` will always send the date and time as a single message, in an attempt to
  mitigate this issue.

* C-Bus time values have an optional "daylight saving time" flag, with three states: "no daylight
  saving offset applied", "time advanced by 1 hour for daylight saving", and "unknown".

  Because this is cannot be used to present daylight saving time properly (eg: Lord Howe Island
  turns their clocks forward 30 minutes for DST), and there are far too many edge cases with
  time zone handling, :program:`cmqttd` will always report "unknown", in an attempt to make sure
  C-Bus units do not attempt any time conversions.

* C-Bus does not support leap seconds. You can mitigate this by synchronising your clock using an
  NTP server with `leap second smearing`__.

__ https://developers.google.com/time/smear

To schedule scenes in C-Bus, you should use something like Home Assistant, rather than embedded
controllers directly attached to the C-Bus network.

.. option:: --timesync SECONDS

    Periodically sends an unsolicited time signal to the C-Bus network.

    By default, this is every 300 seconds (5 minutes).

    If set to ``0``, :program:`cmqttd` will not send unsolicited time signals to the C-Bus network.

.. option:: --no-clock

    Disables responding to time requests from the C-Bus network.

Logging
-------

.. option:: --log-file FILE

    Where to write the log file. If not specified, logs are written to ``stdout``.

.. option:: --verbosity LEVEL

    Verbosity of logging to emit. If not specified, defaults to ``INFO``.

    Options: CRITICAL, ERROR, WARNING, INFO, DEBUG


Using with Home Assistant
=========================

:program:`cmqttd` supports `Home Assistant's MQTT discovery protocol`__.

__ https://www.home-assistant.io/docs/mqtt/discovery/

To use it, just add a MQTT integration using the same MQTT Broker as :program:`cmqttd` with
`discovery enabled`__ (this is *disabled* by default).  See `Home Assistant's documentation`__
for more information and example configurations.

__ https://www.home-assistant.io/docs/mqtt/discovery/
__ https://www.home-assistant.io/docs/mqtt/broker

Once the integration and :program:`cmqttd` are running, each group addresses (regardless of whether
it is in use) will automatically appear in Home Assistant's UI as two components:

* `lights`__: ``light.cbus_{{GROUP_ADDRESS}}`` (eg: GA 1 = ``light.cbus_1``)

  This implements read / write access to lighting controls on the default lighting application.
  "Lighting Ramp" commands can be sent via the standard ``brightness`` and ``transition``
  extensions.

  By default, these will have names like ``C-Bus Light 001``.

* `binary sensors`__: ``binary_sensor.cbus_{{GROUP_ADDRESS}}`` (eg: GA 1 =
  ``binary_sensor.cbus_1``).

  This is a binary, read-only interface for all group addresses.

  An example use case is a PIR (occupancy/motion) sensor that has been configured (in C-Bus
  Toolkit) to actuate two group addresses -- one for the light in the room (shared with an
  ordinary wall switch), and which only reports recent movement.

  :program:`cmqttd` doesn't assign any `class`__ to this component, so this can be used however you
  like. Any brightness value is ignored.

  By default, these will have names like ``C-Bus Light 001 (as binary sensor)``.

__ https://www.home-assistant.io/integrations/light.mqtt/
__ https://www.home-assistant.io/integrations/binary_sensor.mqtt/
__ https://www.home-assistant.io/integrations/binary_sensor/#device-class

All elements can be `renamed and customized`__ from within Home Assistant.

__ https://www.home-assistant.io/docs/configuration/customizing-devices/

.. _cmqttd-docker:

Running in Docker
=================

This repository includes a :file:`Dockerfile`, which uses a minimal `Alpine Linux`__ image as a
base, and contains the *bare minimum* needed to make :program:`cmqttd` work.

__ https://alpinelinux.org/

On a system with Docker installed, clone the `libcbus git repository`__ and then run::

    # docker build -t cmqttd .

__ https://github.com/micolous/cbus

This will download about 120 MiB of dependencies, and result in about 100 MiB image (named
``cmqttd``).

The image's startup script (:file:`entrypoint-cmqttd.sh`) uses the following environment variables:

.. envvar:: TZ

    The timezone to use when sending a time signal to the C-Bus network.

    This must be a `tz database timezone name`__ (eg: ``Australia/Adelaide``). The default (and
    fall-back) timezone is `UTC`__.

__ https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
__ https://en.wikipedia.org/wiki/Coordinated_Universal_Time

.. envvar:: SERIAL_PORT

    The serial port that the PCI is connected to. USB PCIs appear as a serial device
    (``/dev/ttyUSB0``).

    Docker *also* requires the ``--device`` option so that it is forwarded into the container.

    This is equivalent to :option:`cmqttd --serial`. Either this or :envvar:`CNI_ADDR` is required.

.. envvar:: CNI_ADDR

    A TCP ``host:port`` where a CNI is located.

    This is equivalent to :option:`cmqttd --tcp`. Either this or :envvar:`SERIAL_PORT` is required.

    See also: :ref:`Instructions for Wiser users <cmqttd-wiser>`.

.. envvar:: MQTT_SERVER

    IP address where the MQTT Broker is running.

    This is equivalent to :option:`cmqttd --broker-address`. This environment variable is required.

.. envvar:: MQTT_PORT

    Port address where the MQTT Broker is running.

    This is equivalent to :option:`cmqttd --broker-port`.

.. envvar:: MQTT_USE_TLS

    If set to ``1`` (default), this enables support for TLS.

    If set to ``0``, TLS support will be disabled.  This is equivalent to
    :option:`cmqttd --broker-disable-tls`.

.. envvar:: CBUS_CLOCK

    If set to ``1`` (default), :program:`cmqttd` will respond to time requests from the C-Bus
    network.

    If set to ``0``, :program:`cmqttd` will ignore time requests from the C-Bus network. This is
    equivalent to :option:`cmqttd --no-clock`.

.. envvar:: CBUS_TIMESYNC

    Number of seconds to wait between sending an unsolicited time signal to the C-Bus network.

    If set to ``0``, :program:`cmqttd` will not send unsolicited time signals to the C-Bus network.

    By default, this will be sent every 300 seconds (5 minutes).

    This is equivalent to :option:`cmqttd --timesync`.

The image is configured to read additional files from :file:`/etc/cmqttd`, if present. Use
`Docker volume mounts`__ to make the following files available:

__ https://docs.docker.com/engine/reference/commandline/run/#mount-volume--v---read-only

:file:`/etc/cmqttd/auth`
    Username and password to use to connect to an MQTT broker, separated by
    a newline character.

    If this file is not present, then :program:`cmqttd` will try to use the MQTT broker without
    authentication.

    This is equivalent to :option:`cmqttd --broker-auth`.

:file:`/etc/cmqttd/certificates`
    A directory of CA certificates to trust when connecting with TLS.

    If this directory is not present, the default (Python) CA store will be used instead.

    This is equivalent to :option:`cmqttd --broker-ca`.

:file:`/etc/cmqttd/client.pem`, :file:`/etc/cmqttd/client.key`
    Client certificate (``pem``) and private key (``key``) to use to connect to the MQTT broker.

    This is equivalent to :option:`cmqttd --broker-client-cert` and
    :option:`cmqttd --broker-client-key`.

:file:`/etc/cmqttd/project.cbz`
    C-Bus Toolkit project backup file to use as a source for labelling group addresses.

    This is is equivalent to :option:`cmqttd --project-file`.

.. note::

    All file and directory names are case-sensitive, and must be lower case.

Docker usage examples
---------------------

To use a PCI on :file:`/dev/ttyUSB0`, with an unauthenticated and unencrypted MQTT Broker at
``192.0.2.1``, and the time zone set to ``Australia/Adelaide``::

    # docker run --device /dev/ttyUSB0 -e "SERIAL_PORT=/dev/ttyUSB0" \
        -e "MQTT_SERVER=192.0.2.1" -e "MQTT_USE_TLS=0" \
        -e "TZ=Australia/Adelaide" cmqttd

To supply MQTT broker authentication details, create an :file:`/etc/cmqttd/auth` file to be
shared with the container as a `Docker volume`__::

    # mkdir -p /etc/cmqttd
    # touch /etc/cmqttd/auth
    # chmod 600 /etc/cmqttd/auth
    # echo "my-username" >> /etc/cmqttd/auth
    # echo "my-password" >> /etc/cmqttd/auth

__ https://docs.docker.com/engine/reference/commandline/run/#mount-volume--v---read-only

Then to use these authentication details, with TLS enabled::

    # docker run --device /dev/ttyUSB0 -e "SERIAL_PORT=/dev/ttyUSB0" \
        -e "MQTT_SERVER=192.0.2.1" -e "TZ=Australia/Adelaide" \
        -v /etc/cmqttd:/etc/cmqttd cmqttd

If you want to run the ``cmqttd`` daemon in the background, on the same device
as a Home Assistant server with the MQTT broker add-on::

    # docker run -dit --name cbus --restart=always \
        --device /dev/ttyUSB0 --network hassio \
        -e "TZ=Australia/Adelaide" -e "BROKER_USE_TLS=0" \
        -e "SERIAL_PORT=/dev/ttyUSB0" \
        -e "MQTT_SERVER=core-mosquitto" \
        cmqttd

.. note::

    You can verify the hostname of hassio's MQTT broker with:
    ``# docker inspect addon_core_mosquitto``

If you want to run the daemon manually with other settings, you can run ``cmqttd`` manually within
the container (ie: skipping the start-up script) with::

    # docker run -e "TZ=Australia/Adelaide" cmqttd cmqttd --help

.. note::

    When running *without* the start-up script:

    * you must write ``cmqttd`` twice: first as the name of the image, and second as the program
      inside the image to run.

    * none of the environment variables (except :envvar:`TZ`) are supported -- you must use
      :ref:`cmqttd command-line options <cmqttd-options>` instead.

    * files in :file:`/etc/cmqttd` are not used unless equivalent
      :ref:`cmqttd command-line options <cmqttd-options>` are manually specified.
