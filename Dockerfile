FROM alpine:3.11
RUN apk add --no-cache python3 build-base python3-dev py3-cffi
ADD . /cbus
RUN pip3 install -r /cbus/requirements-cmqttd.txt
WORKDIR /cbus
CMD python3 -m cbus.daemon.cmqttd -b ${MQTT_SERVER:?unset} -s ${SERIAL_PORT:?unset}
