*****
Wiser
*****

The Wiser is a rebadged SparkLAN 802.11b/g/draft-n WiFi Router with custom firmware.  Believe it could be either a WRTR-205GN (based on firmware header) or WRTR-502GN (based on what is available information online).  It runs an embedded Linux system, with an expanded web interface for hosting Flash/XMLSocket based control of CBus.

According to the source code release from Clipsal, this runs Linux 2.6.17.14.  The kernel configuration indicates that the board is a ``fv13xx`` ARM system.

This is also used by the iPhone version of the control software.

At the moment this is a rather unorganised set of notes while I'm still figuring out the protocol.

Downloading SWFs
================

First step is you are directed to the page ``/clipsal/resources/wiserui.html``.  This in turn loads the SWF ``/clipsal/resources/wiserui.swf``.

As this is SWF, there is a cross-domain access policy in place to allow the SWF to connect back to the server on other ports::

	<cross-domain-policy><allow-access-from domain="*" secure="false" to-ports="8888,8889"/></cross-domain-policy>

This configuration appears to be one that allows anything to make requests to the Wiser.  So you could write your own implementation of the Wiser control UI and have it connect back, or if you use a well-known address for the Wiser, any Flash applet on the internet could!

The resources and API classes are stored in ``/clipsal/resources/resources.swf``.  This contains things like the cbus_controller class which is used to establish Flash XMLSocket connections.

Protocol
========

Discovery and Handshake
-----------------------

After the SWF is started, it loads the configuration file from ``/clipsal/resources/local_config.xml``.  This looks like::

	<local_config version="1.0"><wiser ip="XXX.XXX.XXX.XXX" port="8888" remote_url="" remote_port="8336" remote="0" wan="0"/><client name="Web UI" fullscreen="0" http_auth="0" local_file_access="1" local_project="0" local_skin_definition="0"/></local_config>

Here we see the internal IP address of the Wiser, and the port that is used for XMLSockets requests.

There is a basic authentication system in place on some of the sockets.  This can be established by retrieving the key from ``/clipsal/resources/projectorkey.xml``.  This file looks like::

	<cbus_auth_data value="0x12345678"/>

.. note::

	It appears that the authentication key is always the same regardless of reboots or different HTTP interface passwords.  As the XMLSocket protocol is out-of-band from the HTTP interface, this is the **only** authentication step performed for clients.
	
	As a result, changing passwords in the web interface are not an effective measure for preventing access to the CBus XMLSocket protocol.
	
	I do not have enough information at this time about Wiser internals to be able to assess how this authentication key is generated.

There is now enough information to connect to the XMLSocket service on port 8888 of the Wiser (or "port" in ``local_config.xml``).
	
So to start the connection we need to send some commands off to the server to handshake.

This starts with a command called ``<cbus_auth_cmd>``.  This has three attributes, required **exactly** in this order::

	<cbus_auth_cmd value="0x12345678" cbc_version="3.7.0" count="0" />

* value is the value of the cbus_auth_data retrieved in the previous step.
* cbc_version is the version of the SWF being used.  This is found in wiserui.swf, in the variable "cbc_version".
* count is the number of times that this session has attempted to authenticate.  Set this to 0.

You could also request the project files and skin files in one shot, like this::

	<cbus_auth_cmd value="0x12345678" cbc_version="3.7.0" count="0" /><project-file-request /><skin-file-request />

The Wiser responds with a message like this::

	<ka cbus_connected="1" /><cbd_version version="Kona_1.24.0" /><net_status cni_transparent="0" cni="1" cftp="1" cbus="1" ntp="0" /><cbus_event app="0xdf" name="cbusTimeChanged" time="120103102012.43" dst="0" ntp="0" />

	
Project and Skin
----------------

It also returns a ``<Touchscreen>`` XML which is a form of the project file, and a ``<skin>`` XML which contains localised strings and resource image references.

This can also be downloaded from ``/clipsal/resources/project.xml`` and ``/clipsal/resources/skin_definition.xml``, so you can just establish a connection without requesting these files over the XMLSocket.  Potentially this could be more reliable.

The project file contains all of the programming in use on the Wiser, button assignments and schedules.  It can also contain additional metadata about the installation, if the installer has filled this in.


XMLSocket protocol for dummies
------------------------------

Adobe's documentation describes the XMLSocket protocol as sending XML documents in either direction on the TCP socket, terminated by a null character.

It is like a simple version of WebSockets -- client and server may send data at any time, there is no synchronous response mechanism, and very easy to implement.

The XML documents sent do not require the typical XML stanzas at the start of the file specifying encoding, and may also contain multiple top-level (document) elements.

There are third-party client and server libraries available for this protocol.

Firmware image
==============

Firmware image for the device is bundled with the PICED software as :file:`Firmware/firmware_1_24_0.img`.  The tool `binwalk`__ shows the layout of the firmware image::

	0x13      	uImage header, header size: 64 bytes, header CRC: 0x2781C02C, created: Mon Oct  3 11:26:33 2011, image size: 722439 bytes, Data Address: 0x40008000, Entry Point: 0x40008000, data CRC: 0xF7547123, OS: Linux, CPU: ARM, image type: OS Kernel Image, compression type: lzma, image name: Linux-2.6.17
	0x53      	LZMA compressed data, properties: 0x5D, dictionary size: 8388608 bytes, uncompressed size: 2015280 bytes
	0xC0013   	Squashfs filesystem, little endian, version 2.1, size: 1736392 bytes, 435 inodes, blocksize: 65536 bytes, created: Mon Oct  3 11:27:23 2011

__ https://code.google.com/p/binwalk/

Appears to be a uBoot image with some extra headers on the image.

Extracting root filesystem
--------------------------

.. highlight:: console

The version of squashfs used by the root filesystem is very old, and current Linux kernels are incapable of mounting it.  It requires an LZMA version of squashfs-2.1 in order to extract it, available from `firmware-mod-kit`__.  Their SVN repository contains all the components needed::

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

* Shell interface from ``console.asp`` accessible on the webserver, however the form on the page is broken.
* NTP client which has 32 hard-coded NTP server IP addresses.
* "FTP" daemon, which appears to be a backdoor into the device, with hard-coded password.

