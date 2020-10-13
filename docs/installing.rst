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

See :ref:`cmqttd-docker`.
