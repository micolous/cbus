# This folder should contain optional cmqttd configuration files.

## project.cbz (file)
This file provides cbus group labels. Create a backup of the cbus project with the cbus setup tool, copy the back up file in this folder and rename it: project.cbz

## auth (file)
Username and password to use to connect to an MQTT broker, separated by a newline character.
If this file is not present, then cmqttd will try to use the MQTT broker without authentication.

## certificates (directory)
A directory of CA certificates to trust when connecting with TLS.
If this directory is not present, the default (Python) CA store will be used instead.

## client.pem  client.key (files)
Client certificate (pem) and private key (key) to use to connect to the MQTT broker.

