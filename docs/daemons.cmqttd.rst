******
cmqttd
******

:program:`cmqttd` allows you to expose a C-Bus network to an MQTT broker. This daemon replaces
:program:`cdbusd` (which required D-Bus) as the abstraction mechanism for all other components.

It uses `Home Assistant`__ style `MQTT-JSON Light components`__, and supports `MQTT discovery`__.
This eliminates the need for ``sage`` (our custom web interface which replaced
:doc:`Wiser <wiser-swf-protocol>`).

__ https://www.home-assistant.io/
__ https://www.home-assistant.io/integrations/light.mqtt/#json-schema
__ https://www.home-assistant.io/docs/mqtt/discovery/

It should also work with other software that supports MQTT.

:program:`cmqttd` with Home Assistant, this has many advantages over :doc:`Wiser <wiser-swf-protocol>`:

- No dependency on Flash Player or a mobile app
- No requirement for an Ethernet-based PCI (serial or USB are sufficient)
- Touch-friendly UI based on Material components
- No hard coded back-doors (like Wiser)

Running
=======

:program:`cmqttd` requires a MQTT Broker (server) to act as a message bus.  We'll assume you have
one running on ``192.0.2.1`` for this example::

    $ python3 -m cbus.daemons.cmqttd -b 192.0.2.1 -s /dev/ttyUSB0

.. note:: :program:`cmqttd` does not yet support authentication or encryption.

Using with Home Assistant
=========================

Add a new ``MQTT`` integration with the same Broker, and enable discovery.  Devices will appear as
``light.cbus_*`` in Home Assistant.
