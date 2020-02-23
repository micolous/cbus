Protocol
========

C-Bus uses it's own protocol in order to send messages over the C-Bus PHY.

This is reflected in the PC Interface protocol.

This package contains classes needed in order to operate with the protocol.

.. note::

    The only "stable" API for this project is the :doc:`C-Bus to MQTT bridge <cmqttd>`, when
    accessed via an MQTT broker.

    The lower level APIs are subject to change without notice, as we learn new information about the
    C-Bus control protocol, and functionality from other applications is brought into the
    :doc:`C-Bus to MQTT bridge <cmqttd>`.

.. toctree::
	:maxdepth: 2
	
	cbus.protocol.base_packet
	cbus.protocol.dm_packet
	cbus.protocol.packet
	cbus.protocol.pm_packet
	cbus.protocol.pp_packet
	cbus.protocol.reset_packet
	cbus.protocol.scs_packet
	cbus.protocol.pciprotocol
	cbus.protocol.pciserverprotocol
	cbus.protocol.application

