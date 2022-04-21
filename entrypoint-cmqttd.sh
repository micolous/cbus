#!/bin/sh
# This script is used as the entrypoint for the cmqttd Docker container. It is not intended for use
# outside of that environment.
#
# This allows passing configuration flags as environment variables, which are more Docker friendly.

# Authentication file for MQTT
CMQTTD_AUTH_FILE="/etc/cmqttd/auth"

# CA certificate directory
CMQTTD_CA_CERT_PATH="/etc/cmqttd/certificates"

# Client certificate, public part
CMQTTD_CLIENT_CERT_PATH="/etc/cmqttd/client.pem"

# Client certificate, private part, must NOT be encrypted
CMQTTD_CLIENT_KEY_PATH="/etc/cmqttd/client.key"

# C-Bus Toolkit project backup file
CMQTTD_PROJECT_FILE="/etc/cmqttd/project.cbz"

# Arguments that are always required.
CMQTTD_ARGS="--broker-address ${MQTT_SERVER:?unset} --timesync ${CBUS_TIMESYNC:-300}"

# Simple arguments
if [ -n "${MQTT_PORT}" ]; then
    CMQTTD_ARGS="${CMQTTD_ARGS} --broker-port ${MQTT_PORT}"
fi

if [ -n "${SERIAL_PORT}" ]; then
    echo "Using serial PCI at ${SERIAL_PORT}"
    CMQTTD_ARGS="${CMQTTD_ARGS} --serial ${SERIAL_PORT}"
elif [ -n "${CNI_ADDR}" ]; then
    echo "Using TCP CNI at ${CNI_ADDR}"
    CMQTTD_ARGS="${CMQTTD_ARGS} --tcp ${CNI_ADDR}"
else
    echo "Either SERIAL_PORT or CNI_ADDR must be specified!"
    exit 1
fi

if [ "${CBUS_CLOCK:-1}" != "1" ]; then
    echo "Not responding to clock requests."
    CMQTTD_ARGS="${CMQTTD_ARGS} --no-clock"
fi

if [ "${MQTT_USE_TLS:-1}" == "1" ]; then
    echo "Using TLS to connect to MQTT broker."

    # Using TLS, check for certificates directory
    if [ -d "${CMQTTD_CA_CERT_PATH}" ]; then
        echo "Using custom certificates in ${CMQTTD_CA_CERT_PATH}"
        CMQTTD_ARGS="${CMQTTD_ARGS} --broker-ca ${CMQTTD_CA_CERT_PATH}"
    else
        echo "${CMQTTD_CA_CERT_PATH} not found, using Python CA store."
    fi

    # Client certificates
    if [ -e "${CMQTTD_CLIENT_CERT_PATH}" ] && [ -e "${CMQTTD_CLIENT_KEY_PATH}" ]; then
        echo "Using client cert: ${CMQTTD_CLIENT_CERT_PATH}"
        echo "Using client key: ${CMQTTD_CLIENT_KEY_PATH}"
        CMQTTD_ARGS="${CMQTTD_ARGS} --broker-client-cert ${CMQTTD_CLIENT_CERT_PATH} --broker-client-key ${CMQTTD_CLIENT_KEY_PATH}"
    else
        echo -n "${CMQTTD_CLIENT_CERT_PATH} and/or ${CMQTTD_CLIENT_KEY_PATH} not found, not using "
        echo "client certificates for authentication."
    fi
else
    echo "Disabling TLS support. This is insecure!"
    CMQTTD_ARGS="${CMQTTD_ARGS} --broker-disable-tls"
fi

if [ -e "${CMQTTD_AUTH_FILE}" ]; then
    echo "Using MQTT login details in ${CMQTTD_AUTH_FILE}"
    CMQTTD_ARGS="${CMQTTD_ARGS} --broker-auth ${CMQTTD_AUTH_FILE}"
else
    echo "${CMQTTD_AUTH_FILE} not found; skipping MQTT authentication."
fi

if [ -e "${CMQTTD_PROJECT_FILE}" ]; then
    echo "Using C-Bus Toolkit project backup file ${CMQTTD_PROJECT_FILE}"
    CMQTTD_ARGS="${CMQTTD_ARGS} --project-file ${CMQTTD_PROJECT_FILE}"
else
    echo "${CMQTTD_PROJECT_FILE} not found; using generated labels."
fi

if [ -n "${CBUS_NETWORK}" ]; then
    echo "Using first project in network file if it exists"
else 
    echo "Using project ${CBUS_NETWORK} if it exists"
    CMQTTD_ARGS="${CMQTTD_ARGS} --cbus-network '${CBUS_NETWORK}'"
fi

echo ""

# Announce what we think local time is on start-up. This will be sent to the C-Bus network.
echo "Local time zone: ${TZ:-UTC}"
echo -n "Current time: "
date -R

echo "Running with flags: ${CMQTTD_ARGS}"
cmqttd $CMQTTD_ARGS
