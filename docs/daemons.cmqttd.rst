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
- No hard coded back-doors (like Wiser)

.. note:: Only the lighting application is supported by :program:`cmqttd`. Patches welcome!

Running
=======

:program:`cmqttd` requires a MQTT Broker (server) to act as a message bus.  We'll assume you have
one running on ``192.0.2.1``, and USB or serial PCI connected on ``/dev/ttyUSB0`` for this example::

    $ python3 -m cbus.daemons.cmqttd -b 192.0.2.1 -s /dev/ttyUSB0

.. note::

    :program:`cmqttd` uses TLS to connect to your MQTT Broker by default.  If you want to disable
    TLS, add the ``--broker-disable-tls`` option.

Time synchronisation
--------------------

By default, :program:`cmqttd` will periodic provide a time signal to the C-Bus network, and respond
to time requests.  For systems that do not have a reliable time source, or if you already have some
other device providing a time signal, this can be _disabled_ with::

    $ python3 -m cbus.daemons.cmqttd -b 192.0.2.1 -s /dev/ttyUSB0 --timesync 0 --no-clock

Local time is always used for time synchronisation.  You can specify a different timezone with
`the TZ environment variable`__.

__ https://www.gnu.org/software/libc/manual/html_node/TZ-Variable.html

Using with Home Assistant
-------------------------

Add a new MQTT integration with the same Broker as what you used for :program:`cmqttd`, and
`enable discovery`__.  Lights will appear as ``light.cbus_`` followed by their group address (eg:
``light.cbus_1``).

__ https://www.home-assistant.io/docs/mqtt/discovery/

By default, these will have names like ``CBus Light 001`` -- but this can be renamed from within
Home Assistant.
