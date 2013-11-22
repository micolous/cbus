****
sage
****

sage is a web interface for lighting controls, similar to :doc:`Wiser <wiser-swf-protocol>`, except it doesn't suck:

- It has no dependancy on Flash player or a device-specific app (it uses WebSockets instead).
- It has a very minimalist, touch-friendly UI based on jQuery Mobile.
- It works as a "web app" on iOS 4.2 and later (due to patchy WebSockets support).
- It has no requirement for a ethernet-based PCI (serial/USB are fine).
- It doesn't have hard coded backdoors and changing the password actually locks previous users out.  (However some browsers don't implement support for HTTP Authentication requests on WebSockets)

It connects to :doc:`daemons.cdbusd <cdbusd>` as it's abstraction layer, and only presents lighting events to clients.

It is made of some parts:

- ``saged`` which is a backend WebSockets server that translates WebSockets messages into messages in cdbusd, and implements some basic access controls.
- ``sageclient.js`` which implements the saged WebSockets protocol in JavaScript.
- ``sageui.js`` which implements the UI of sage itself, which is built on jQuery Mobile.

