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

    For these examples, we'll assume your MQTT server:

    - is accessible via ``192.0.2.1`` on the default port (1883).
    - does not use transport security (TLS)
    - does not require authentication

    This setup is not secure -- but securing your MQTT server is out of the scope of this document.

    Run :program:`cmqttd` with the ``--help`` option to get a full list of options, which describe
    how to set up authentication, certificate validation and transport security.

To connect to a serial or USB PCI connected on ``/dev/ttyUSB0``, run::

    $ python3 -m cbus.daemons.cmqttd -b 192.0.2.1 --broker-disable-tls -s /dev/ttyUSB0

To connect to a CNI (or PCI over TCP) listening at ``192.0.2.2:10001``, run::

    $ python3 -m cbus.daemons.cmqttd -b 192.0.2.1 --broker-disable-tls -s /dev/ttyUSB0

.. warning::

    The ``--broker-disable-tls`` *disables all transport security* (TLS).

    By default, :program:`cmqttd` will connect to your MQTT broker using TLS.

Time synchronisation
--------------------

By default, :program:`cmqttd` will periodic provide a time signal to the C-Bus network, and respond
to all time requests.

Local time is always used for time synchronisation.  You can specify a different timezone with
`the TZ environment variable`__. Due to C-Bus protocol limitations, no attempt is made to allow
units on the C-Bus network to configure the timezone provided by :program:`cmqttd`.

__ https://www.gnu.org/software/libc/manual/html_node/TZ-Variable.html

For systems that do not have a reliable time source, or if you already have some other device
providing a time signal, this can be *disabled* with::

    $ python3 -m cbus.daemons.cmqttd -b 192.0.2.1 -s /dev/ttyUSB0 --timesync 0 --no-clock

Using with Home Assistant
-------------------------

:program:`cmqttd` supports `Home Assistant's MQTT discovery protocol`__.

__ https://www.home-assistant.io/docs/mqtt/discovery/

To use it, just add a MQTT integration using the same MQTT Broker as :program:`cmqttd` with
`discovery enabled`__ (this is *disabled* by default).  See `Home Assistant's documentation`__
for more information and example configurations.

__ https://www.home-assistant.io/docs/mqtt/discovery/
__ https://www.home-assistant.io/docs/mqtt/broker

Once the integration and :program:`cmqttd` are running, each group addresses (regardless of whether
it is in use) will automatically appear in Home Assistant's UI as _two_ components:

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
