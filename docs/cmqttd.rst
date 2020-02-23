******
cmqttd
******

:program:`cmqttd` allows you to expose a C-Bus network to an MQTT broker. This daemon replaces
:program:`cdbusd` (which required D-Bus) as the abstraction mechanism for all other components.

It uses `Home Assistant`__ style `MQTT-JSON Light components`__, and supports `MQTT discovery`__.
This replaces :program:`sage` (our custom web interface which replaced
:doc:`Wiser <wiser-swf-protocol>`).

__ https://www.home-assistant.io/
__ https://www.home-assistant.io/integrations/light.mqtt/#json-schema
__ https://www.home-assistant.io/docs/mqtt/discovery/

It should also work with other software that supports MQTT.

:program:`cmqttd` with Home Assistant has many advantages over :doc:`Wiser <wiser-swf-protocol>`:

- No dependency on Flash Player or a mobile app
- No requirement for an Ethernet-based PCI (serial or USB are sufficient)
- Touch-friendly UI based on Material components
- Integrates with other Home Assistant supported devices
- No :ref:`hard coded back-doors <wiser-backdoor>`

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

To connect to a serial or USB PCI connected on ``/dev/ttyUSB0``, run::

    $ cmqttd -b 192.0.2.1 --broker-disable-tls -s /dev/ttyUSB0

To connect to a CNI (or PCI over TCP) listening at ``192.0.2.2:10001``, run::

    $ cmqttd -b 192.0.2.1 --broker-disable-tls -s /dev/ttyUSB0

.. tip::

    If you haven't :doc:`installed the library <installing>`, you can run from a ``git clone`` of
    ``libcbus`` source repository with::

        $ python3 -m cbus.daemons.cmqttd -b 192.0.2.1 [...]

Configuration
=============

:program:`cmqttd` has many command-line configuration options.

A complete list can be found by running ``cmqttd --help``.

C-Bus PCI options
-----------------

One of these *must* be specified:

``--serial [device]``
    Serial device that the PCI is connected to, eg: ``/dev/ttyUSB0``.

    USB PCIs (5500PCU) act as a SiLabs ``cp210x`` USB-Serial adapter, its serial device must be
    specified here.

``--tcp [addr]:[port]``
    IP address and TCP port where the PCI or CNI is located, eg: ``192.0.2.1:10001``.

    Both the address and the port are required. CNIs listen on port ``10001`` by default.


.. _mqtt-options:

MQTT options
------------

``--broker-address [addr]``
    Address of the MQTT broker. This option is required.

``--broker-port [port]``
    Port of the MQTT broker.

    By default, this is 8883 if TLS is enabled, otherwise 1883.

``--broker-disable-tls``
    Disables all transport security (TLS). This option is insecure!

    By default, transport security is enabled.

``--broker-auth [file]``
    File containing the username and password to authenticate to the MQTT broker with.

    This is a plain text file with two lines: the username, followed by the password.

    If not specified, password authentication will not be used.

``--broker-ca [dir]``
    Path to a directory of CA certificates to trust, used for validating certificates presented in
    the TLS handshake.

    If not specified, the default (Python) CA store is used instead.

``--broker-client-cert [pem]``

``--broker-client-key [pem]``
    Path to a PEM-encoded client (public) certificate and (private) key for TLS authentication.

    If not specified, certificate-based client authentication will not be used.

    If the file is encrypted, Python will prompt for the password at the command-line.

Time synchronisation
--------------------

By default, :program:`cmqttd` will periodic provide a time signal to the C-Bus network, and respond
to all time requests.

``--timesync [seconds]``
    Sends an unsolicited time signal to the C-Bus network.

    By default, this is every 300 seconds (5 minutes).

``--timesync 0``
    Disables sending unsolicited time signals to the C-Bus network.

``--no-clock``
    Disables responding to time requests from the C-Bus network.

Local time is always used for time synchronisation. You can specify a different timezone with
`the TZ environment variable`__.

__ https://www.gnu.org/software/libc/manual/html_node/TZ-Variable.html

Due to C-Bus protocol limitations, no attempt is made to allow units on the C-Bus network to
configure the timezone provided by :program:`cmqttd`.

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
