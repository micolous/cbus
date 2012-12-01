****************************
Wiser SWF XMLSocket Protocol
****************************

At the moment this is a rather unorganised set of notes while I'm still figuring out the protocol.

First step is you are directed to the page ``/clipsal/resources/wiserui.html``.  This in turn loads the SWF ``/clipsal/resources/wiserui.swf``.

As this is SWF, there is a cross-domain access policy in place:

	<cross-domain-policy><allow-access-from domain="*" secure="false" to-ports="8888,8889"/></cross-domain-policy>

This loads the configuration file from ``/clipsal/resources/local_config.xml``.  This looks like::

	<local_config version="1.0"><wiser ip="XXX.XXX.XXX.XXX" port="8888" remote_url="" remote_port="8336" remote="0" wan="0"/><client name="Web UI" fullscreen="0" http_auth="0" local_file_access="1" local_project="0" local_skin_definition="0"/></local_config>

This leads me to the conclusion the control port is 8888.  Has interesting side-effect that if you have supplied authentication details to Wiser, it will allow any site on the internet to control the unit...

The resources and API classes are stored in ``/clipsal/resources/resources.swf``.  This contains things like the cbus_controller class which is used to establish Flash XMLSocket connections.

There is a basic authentication system in place on some of the sockets.  This can be established by retrieving the key from ``/clipsal/resources/projectorkey.xml``.  This file looks like::

	<cbus_auth_data value="0x12345678"/>

Adobe's documentation describes the XMLSocket protocol as sending XML documents in either direction on the TCP socket, terminated by a null character.

So to start the connection we need to send some commands off to the server to handshake.

This starts with a command called ``<cbus_auth_cmd>``.  This has three attributes, required **exactly** in this order::

	<cbus_auth_cmd value="0x12345678" cbc_version="3.7.0" count="0" />

  * value is the value of the cbus_auth_data retrieved in the previous step.
  * cbc_version is the version of the SWF being used.  This is found in wiserui.swf, in the variable "cbc_version".
  * count is the number of times that this session has attempted to authenticate.  Set this to 0.

You could also request the project files and skin files in one shot, like this:

	<cbus_auth_cmd value="0x12345678" cbc_version="3.7.0" count="0" /><project-file-request /><skin-file-request />

The Wiser responds with a message like this::

	<ka cbus_connected="1" /><cbd_version version="Kona_1.24.0" /><net_status cni_transparent="0" cni="1" cftp="1" cbus="1" ntp="0" /><cbus_event app="0xdf" name="cbusTimeChanged" time="120103102012.43" dst="0" ntp="0" />

It also returns a ``<Touchscreen>`` XML which is a form of the project file, and a ``<skin>`` XML which contains localised strings and resource image references.

This can also be downloaded from ``/clipsal/resources/project.xml`` and ``/clipsal/resources/skin_definition.xml``, so you can just establish a connection without requesting these files over the XMLSocket.  Potentially this could be more reliable.

