#!/bin/sh

install -o0 -g0 platform/debian/init.d/cdbusd /etc/init.d/
install -o0 -g0 -m0644 platform/debian/default/cdbusd /etc/default/

