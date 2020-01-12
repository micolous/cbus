*****
Wiser
*****

.. note::

    This is an incomplete collection of notes from reverse engineering the Wiser's firmware.

    It has not been actively worked on in some years, and the author no longer has access to Wiser
    hardware.

    This library **is not** capable of running on Wiser -- and this project's
    :doc:`C-Bus to MQTT bridge <daemons.cmqttd>` can be used with `Home Assistant`__ and entirely
    replaces the need for Wiser.

    It is provided in the hope it could be useful to others, and to serve as a warning against
    using Wiser hardware.

__ https://www.home-assistant.io/docs/mqtt/discovery/

The Wiser is a re-badged `SparkLAN WRTR-501`__ 802.11b/g/draft-n WiFi Router with custom firmware.
It runs an embedded Linux system, with an expanded web interface for hosting Flash/XMLSocket based
control of C-Bus.

__ http://www.sparklan.com/download/wrtr_501_11n_ap_router.pdf

According to the source code release from Clipsal, this runs Linux 2.6.17.14. The kernel
configuration indicates that the board is a ``fv13xx`` ARM system. This is also used by:

* Airlink101 AR680W
* PCi MZK-W04N

XMLSocket is also used by the iPhone version of the control software.

.. note::

    In XML outputs in this document, new-line characters and basic formatting whitespace has been
    added to improve readability. The original data does not contain this, unless otherwise
    indicated.

Downloading SWFs
================

First step is you are directed to the page ``/clipsal/resources/wiserui.html``.  This in turn loads
the SWF ``/clipsal/resources/wiserui.swf``.

.. highlight:: xml

As this is SWF, there is a cross-domain access policy in place to allow the SWF to connect back to the server on other ports::

	<cross-domain-policy>
	  <allow-access-from domain="*" secure="false" to-ports="8888,8889"/>
	</cross-domain-policy>

This configuration **disables all cross-domain security** for requests to the Wiser. You could use
this to write your own implementation of the Wiser control UI and have it connect back to Wiser's
IP. This could also be used to allow any website on the internet you visit to make cross-origin
requests to your browser.

The resources and API classes are stored in ``/clipsal/resources/resources.swf``.  This contains
things like the ``cbus_controller`` class which is used to establish Flash XMLSocket connections.

Protocol
========

Discovery and Handshake
-----------------------

After the SWF is started, it loads the configuration file from ``/clipsal/resources/local_config.xml``.  This looks like::

	<local_config version="1.0">
	  <wiser ip="XXX.XXX.XXX.XXX" port="8888" remote_url="" remote_port="8336"
	         remote="0" wan="0"/>
	  <client name="Web UI" fullscreen="0" http_auth="0" local_file_access="1"
	          local_project="0" local_skin_definition="0"/>
	</local_config>

Here we see the internal IP address of the Wiser, and the port that is used for XMLSockets requests (``port``).  ``remote_port`` indicates the port used by the CFTP daemon.

Authentication
--------------

There is a basic authentication system in place on some of the sockets. This can be established by
retrieving the key from ``/clipsal/resources/projectorkey.xml``. This file looks like::

	<cbus_auth_data value="0x12345678"/>

This projector key is generated when a project file is first created by PICED. The projector key
is **static for all projects created during a particular execution of PICED**.

Rebooting Wiser or changing the HTTP password **never changes this key**. Once someone has this
key, they can use it to access Wiser over XMLSocket **in perpetuity**.

The only way to change it is to re-start PICED (if it was already running), create an entirely new
project file, and transfer this to the Wiser.

Connecting
----------

There is now enough information to connect to the XMLSocket service on port 8888 of the Wiser (or
"port" in ``local_config.xml``).
	
So to start the connection we need to send some commands off to the server to handshake.

This starts with a command called ``<cbus_auth_cmd>``.  This has three attributes, required
**exactly** in this order::

	<cbus_auth_cmd value="0x12345678" cbc_version="3.7.0" count="0" />

* ``value`` is the value of the ``cbus_auth_data`` retrieved in the previous step.
* ``cbc_version`` is the version of the SWF being used.  This is found in ``wiserui.swf``, in the
  variable ``cbc_version``.
* ``count`` is the number of times that this session has attempted to authenticate. Set this to 0.

You could also request the project files and skin files in one shot, like this::

	<cbus_auth_cmd value="0x12345678" cbc_version="3.7.0" count="0" />
	<project-file-request />
	<skin-file-request />

The Wiser responds with a message like this::

	<ka cbus_connected="1" />
	<cbd_version version="Kona_1.24.0" />
	<net_status cni_transparent="0" cni="1" cftp="1" cbus="1" ntp="0" />
	<cbus_event app="0xdf" name="cbusTimeChanged" time="120103102012.43" dst="0" ntp="0" />
	
Project and Skin
----------------

It also returns a ``<Touchscreen>`` XML which is a form of the project file, and a ``<skin>`` XML
which contains localised strings and resource image references.

This can also be downloaded from ``/clipsal/resources/project.xml`` and
``/clipsal/resources/skin_definition.xml``, so you can just establish a connection without
requesting these files over the XMLSocket. Potentially this could be more reliable.

The project file contains all of the programming in use on the Wiser, button assignments and
schedules. It can also contain additional metadata about the installation, if the installer has
filled this in.

XMLSocket protocol for dummies
------------------------------

Adobe's documentation describes the XMLSocket protocol as sending XML documents in either direction
on the TCP socket, terminated by a null character.

It is like a simple version of WebSockets -- client and server may send data at any time, there is
no synchronous response mechanism, and very easy to implement.

The XML documents sent do not require the typical XML stanzas at the start of the file specifying
encoding, and may also contain multiple top-level (document) elements.

There are third-party client and server libraries available for this protocol.

Getting a shell
===============

.. highlight:: console

There is console access available via a web interface on the Wiser, using ``/console.asp``.  It
appears to be taken from some Belkin or Linksys reference firmware image.

Redirection of output to a file using ``>`` doesn't work correctly in the shell.  Regular pipes
(``|``) do work.

Only ``stdout`` is displayed, not ``stderr``.

NVRAM
-----

You can dump the NVRAM::

	$ nvram show
	...
	wan_proto=dhcp
	wan_ipaddr=0.0.0.0
	wan_netmask=0.0.0.0
	wan_gateway=0.0.0.0
	wan_winsserv=
	...


CFTP
====

CFTP is a service which acts as a back-door into the device. It runs on port 8336, and is managed
by the service :program:`cftp_daemon`.

It has a hard-coded password (``bloop``) to access the service.

Despite the name, it doesn't actually implement FTP -- it is used by Clipsal's programming software
in order to manage the device. It appears to have the following functionality:

* Manage port forwards inside of the network when the device is acting as the router for the network.  Unknown how this is controlled.
* Reflash the contents of partition 6 of FLASH (label: ``clipsal``).  Appears to be a gzip-compressed tarball, which gets extracted to :file:`/www/clipsal/resources`.

Communication with the server is done with a simple text-based protocol, with the UNIX newline
character indicating the end of command. DOS or other style line feeds do not work.

If the daemon does not understand your command, it will simply send no response.

Startup process
---------------

On startup, the process will:

1. Delete :file:`/tmp/*.tar.gz`.
2. Copy the contents of :file:`/dev/mtblock/6` to :file:`/tmp/test.cta`.
3. Mount a new ramfs to :file:`/www/clipsal/resources/`
4. Extract :file:`settings.conf` from the gzip-compressed tarball :file:`/tmp/test.cta` to :file:`/www/clipsal/resources/`.
5. Read daemon configuration from :file:`settings.conf`.
6. Extract all files from the tarball to :file:`/www/clipsal/resources/`.

.. highlight:: none

Unauthenticated state
---------------------

Connecting to the service yields a welcome message::

	200 Welcome

PASS
^^^^

Client command::

	PASS bloop

The server will respond that you are logged in successfully, and transition your connection to the
authenticated state::

	201 Logged in

.. note::

    There is no way to change this password.  It is hard coded in Wiser's firmware.

	Sending other passwords yield no response.

Authenticated state
-------------------

When in the authenticated state, the network code appears to be far less robust. Sending large
commands causes the daemon to crash.

This may be an effective and easy way to disable :program:`cftp_daemon` on the device.

PASS
^^^^

Client command::

	PASS bloop

Server response::

	201 Logged in

Transitions to the authenticated state.  Has no effect in authenticated mode.

.. note:: There is no way to change this password.  It is hard coded in Wiser's firmware.

	Sending other passwords yield no response.

VERINFO
^^^^^^^

Client command::

	VERINFO

Server response::

	202-HomeGateVersion=4.0.41.0
	202-CTCServerVersion=Kona_1.24.0
	202-UnitName=EXAMPLE
	202 WindowsOSVersion=5.1.2600 Service Pack 2

Retrieves information about the version of CFTP running on the Wiser, and the C-Bus network's
project name.

The ``WindowsOSVersion`` information is a hard-coded string.

HGSTATUS
^^^^^^^^

Client command::

	HGSTATUS

Server response::

	202-HGRUNNING=False
	202-HGLOGGING=False
	202 CURRPROJ=C:\HomeGate\Projects\Current\EXAMPLEproj.tar.gz

Retrieves the current project name running on the Wiser, and status of "HG"?  This is hard coded to
always return False to both HGRUNNING and HGLOGGING.

The path is faked by the daemon, with "EXAMPLE" replaced by the project name.


GETFILELIST
^^^^^^^^^^^

Client command::

	GETFILELIST

Server response::

	202 FILE1=C:\HomeGate\Projects\Current\EXAMPLEproj.tar.gz

Retrieves a list of "files" on the device associated with the project. This only returns the
project file.

The path is faked by the daemon, with "EXAMPLE" replaced by the project name.

GETPROJ
^^^^^^^

Client command::

	GETPROJ

Server response::

	202-Port=8337
	202 FILE=C:\HomeGate\Projects\Current\EXAMPLEproj.tar.gz

Returns the "project filename" for the contents of flash partition 6. The path information is hard
coded and fake, with "EXAMPLE" replaced by the project name.


INSTALL
^^^^^^^

Client command::

	INSTALL PROJECT example.tar.gz

Server response::

	202 Port=8337

Starts an out of band transfer for overwriting the Wiser's project file.

The server opens up another TCP server on a different port (on Wiser, this is always 8337) in order
to accept the file transfer out of band.


Project file transfer
---------------------

Project file transfer is done on another port (always 8337), and initiated by the ``INSTALL``
command.

The client immediately sends::

	FILE example.tar.gz

This is then immediately followed by a UNIX newline character, and then the file length as a 32-bit
unsigned big-endian integer.

Files must not be bigger than 512kB, or the transfer will be rejected by the Wiser. File names must
end in ``.tar.gz``.

Projects must also not extract to a size greater than about 1 MiB: Wiser stores the contents of
this archive in ramfs, so larger archives will use all available RAM on the Wiser, and cannot be
freed, leading to Linux's oomkiller to run or processes to fail to dynamically allocate memory.
This has the potential in turn to partially brick the Wiser -- :program:`cftp_daemon` will not be
able to copy a new project file into RAM temporarily for flashing, and may be permanently stuck in
this state. This partial brick state could probably gotten around by writing NULL over the contents
of :file:`/dev/mtdblock/6`, then transferring a new project file.


Firmware image
==============

Firmware image for the device is bundled with the PICED software as
:file:`Firmware/firmware_1_24_0.img`.

The tool `binwalk`__ shows the layout of the firmware image::

	0x13        uImage header, header size: 64 bytes, header CRC: 0x2781C02C,
	            created: Mon Oct  3 11:26:33 2011, image size: 722439 bytes,
	            Data Address: 0x40008000, Entry Point: 0x40008000,
	            data CRC: 0xF7547123, OS: Linux, CPU: ARM,
	            image type: OS Kernel Image, compression type: lzma,
	            image name: Linux-2.6.17
	
	0x53        LZMA compressed data, properties: 0x5D,
	            dictionary size: 8388608 bytes, uncompressed size: 2015280 bytes
	
	0xC0013     Squashfs filesystem, little endian, version 2.1,
	            size: 1736392 bytes, 435 inodes, blocksize: 65536 bytes,
	            created: Mon Oct  3 11:27:23 2011

__ https://github.com/ReFirmLabs/binwalk

Appears to be a uBoot image with some extra headers on the image.

Extracting root filesystem
--------------------------

.. highlight:: console

.. warning::

    The links in this section are broken as Google Code has shut down.

The version of squashfs used by the root filesystem is very old, and current Linux kernels are
incapable of mounting it. It requires an LZMA version of squashfs-2.1 in order to extract it,
available from `firmware-mod-kit`__. Their SVN repository contains all the components needed::

	$ svn co https://firmware-mod-kit.googlecode.com/svn/trunk/src/lzma/
	$ svn co https://firmware-mod-kit.googlecode.com/svn/trunk/src/squashfs-2.1-r2/
	$ cd squashfs-2.1-r2
	$ make

__ https://code.google.com/p/firmware-mod-kit/

Once built, extract the root filesystem with::

	$ binwalk -D squashfs:squashfs firmware_1_24_0.img
	$ ./squashfs-2.1-r2/unsquashfs-lzma C0013.squashfs

This will then give an extracted copy of the root filesystem in the directory :file:`squashfs-root`.

Filesystem observations
-----------------------

These are things that need some more investigation:

* NTP client which has 32 hard-coded NTP server IP addresses.
