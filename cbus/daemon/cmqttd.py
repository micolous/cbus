#!/usr/bin/env python3
# cmqttd.py - MQTT connector for C-Bus
# Copyright 2019 Michael Farrell <micolous+git@gmail.com>
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

from argparse import ArgumentParser
import json
import sys
from typing import Any, Dict, Text

import paho.mqtt.client as mqtt

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.protocol import ClientFactory
from twisted.internet.serialport import SerialPort
from twisted.python import log

from cbus.protocol.pciprotocol import PCIProtocol
from cbus.common import MIN_GROUP_ADDR, MAX_GROUP_ADDR, check_ga


def ga_range():
    return range(MIN_GROUP_ADDR, MAX_GROUP_ADDR + 1)


class CBusHandler(PCIProtocol):
    """
    Glue to wire events from the PCI onto MQTT
    """
    cbus_api = None
    mqtt_api = None

    def on_confirmation(self, code, success):
        if not self.cbus_api:
            return
        self.cbus_api.on_confirmation(code, success)

    def on_reset(self):
        if not self.cbus_api:
            return
        self.cbus_api.on_reset()

    def on_mmi(self, application, data):
        if not self.cbus_api:
            return
        self.cbus_api.on_mmi(application, data)

    def on_lighting_group_ramp(self, source_addr, group_addr, duration, level):
        if not self.cbus_api:
            return
        self.cbus_api.on_lighting_group_ramp(source_addr, group_addr, duration,
                                             level)

    def on_lighting_group_on(self, source_addr, group_addr):
        if not self.mqtt_api:
            return
        self.mqtt_api.lighting_group_on(source_addr, group_addr)

    def on_lighting_group_off(self, source_addr, group_addr):
        if not self.mqtt_api:
            return
        self.mqtt_api.lighting_group_off(source_addr, group_addr)

    # TODO: on_lighting_group_terminate_ramp

    def timesync(self, frequency):
        # setup timesync in the future.
        reactor.callLater(frequency, self.timesync, frequency)

        # send time packets
        log.msg('send time')
        self.clock_datetime()

    def on_clock_request(self, source_addr):
        self.clock_datetime()


_TOPIC_PREFIX = 'homeassistant/light/cbus_'
_TOPIC_SET_SUFFIX = '/set'
_TOPIC_CONF_SUFFIX = '/config'
_TOPIC_STATE_SUFFIX = '/state'


class MqttClient(mqtt.Client):

    def on_connect(self, client, userdata: CBusHandler, flags, rc):
        log.msg('Connected to MQTT broker')
        userdata.mqtt_api = self
        self.subscribe([(_TOPIC_PREFIX + str(t) + _TOPIC_SET_SUFFIX, 2)
                        for t in ga_range()])
        self.publish_all_lights()

    def loop_twisted(self) -> None:
        # TODO: tie into twisted reactor properly
        ret = self.loop(timeout=0)
        if ret != mqtt.MQTT_ERR_SUCCESS:
            log.err("MQTT connector error", mqtt.error_string(ret))
            reactor.stop()
            return

        reactor.callLater(1, self.loop_twisted)

    def on_message(self, client, userdata: CBusHandler, msg: mqtt.MQTTMessage):
        if not (msg.topic.startswith(_TOPIC_PREFIX) and
                msg.topic.endswith(_TOPIC_SET_SUFFIX)):
            return

        try:
            ga = int(msg.topic[len(_TOPIC_PREFIX):][:-len(_TOPIC_SET_SUFFIX)])
            check_ga(ga)
        except ValueError:
            # Invalid group address
            log.msg(f'Invalid group address in topic {msg.topic}')
            return

        # process the message per homeassistant JSON
        payload = json.loads(msg.payload)
        light_on = payload['state'].upper() == 'ON'
        brightness = payload.get('brightness', 255) / 255.
        if brightness < 0.:
            brightness = 0.
        if brightness > 1.:
            brightness = 1.
        transition_time = int(payload.get('transition', 0))
        if transition_time < 0:
            transition_time = 0

        if light_on:
            if brightness == 1. and transition_time > 0:
                # lighting on
                userdata.lighting_group_on(ga)
            else:
                # ramp
                userdata.lighting_group_ramp(ga, 1, brightness)
        else:
            # lighting off
            userdata.lighting_group_off(ga)

    def publish(self, topic: Text, payload: Dict[Text, Any], qos: int = 0,
                retain: bool = False):
        payload = json.dumps(payload)
        return super().publish(topic, payload, qos, retain, properties=None)

    def publish_all_lights(self):
        for ga in ga_range():
            self.publish(_TOPIC_PREFIX + str(ga) + _TOPIC_CONF_SUFFIX, {
                '~': _TOPIC_PREFIX + str(ga),
                'name': f'CBus Light {ga:03d}',
                'unique_id': f'cbus_light_{ga}',
                'cmd_t': '~' + _TOPIC_SET_SUFFIX,
                'stat_t': '~' + _TOPIC_STATE_SUFFIX,
                'schema': 'json',
                'brightness': True,
                #'device': {
                #    'identifiers': f'cbus_{ga}',
                #    'connections': [['cbus_group_address', str(ga)]],
                #    'sw_version': 'cmqttd',
                #},
            }, 1, True)

    def lighting_group_on(self, source_addr: int, group_addr: int):
        topic = _TOPIC_PREFIX + str(group_addr) + _TOPIC_STATE_SUFFIX
        self.publish(topic, {
            'state': 'ON',
            'brightness': 255,
            'transition': 0,
            'cbus_source_addr': source_addr,
        })

    def lighting_group_off(self, source_addr: int, group_addr: int):
        topic = _TOPIC_PREFIX + str(group_addr) + _TOPIC_STATE_SUFFIX
        self.publish(topic, {
            'state': 'OFF',
            'brightness': 0,
            'transition': 0,
            'cbus_source_addr': source_addr,
        })






class PCIProtocolFactory(ClientFactory):

    def __init__(self, timesync: int = 10, disable_clock: bool = False):
        self._timesync = timesync
        self.protocol = CBusHandler()
        if disable_clock:
            self.protocol.on_clock_request = lambda *_, **__: None

    def buildProtocol(self, addr=None):
        log.msg('Connected to PCI.')
        if self._timesync:
            reactor.callLater(
                10, self.protocol.timesync, self._timesync)

        return self.protocol

    def clientConnectionLost(self, connector, reason):
        log.err('Lost connection.  Reason:', reason)
        reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        log.err('Connection failed. Reason:', reason)
        reactor.stop()


def main():
    parser = ArgumentParser()

    group = parser.add_argument_group('Daemon options')
    group.add_argument(
        '-D', '--daemon',
        dest='daemon', action='store_true', default=False,
        help='Start as a daemon [default: %(default)s]')

    group.add_argument(
        '-P', '--pid',
        dest='pid_file', default='/var/run/cdbusd.pid',
        help='Location to write the PID file. Only has effect in daemon mode. '
             '[default: %(default)s]'
    )

    group.add_argument(
        '-l', '--log-file',
        dest='log', default=None,
        help='Destination to write logs [default: stdout]')

    group = parser.add_argument_group('MQTT options')
    group.add_argument(
        '-b', '--broker-address',
        required=True,
        help='Address of the MQTT broker',
    )

    group.add_argument(
        '-p', '--broker-port',
        type=int, default=1883,  # TODO: TLS
        help='Port to use to connect to the MQTT broker',
    )

    group.add_argument(
        '--broker-keepalive',
        type=int, default=60,
    )

    # TODO: Authentication
    # TODO: TLS

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        '-s', '--serial-pci',
        dest='serial_pci', default=None,
        help='Serial port where the PCI is located. Either this or -t must be '
             'specified.'
    )

    group.add_argument(
        '-t', '--tcp-pci',
        dest='tcp_pci', default=None,
        help='IP address and TCP port where the PCI is located (CNI). Either '
             'this or -s must be specified.'
    )

    group = parser.add_argument_group('Extras')
    group.add_argument(
        '-T', '--timesync',
        dest='timesync', type=int, default=10,  # TODO: 300s
        help='Send time synchronisation packets every n seconds '
             '(or 0 to disable). [default: %(default)s seconds]'
    )

    group.add_argument(
        '-C', '--no-clock',
        dest='no_clock', action='store_true',
        default=False,
        help='Do not respond to Clock Request SAL messages with the system '
             'time (ie: do not provide the CBus network the time when '
             'requested). Enable if your machine does not have a reliable '
             'time source, or you have another device on the CBus network '
             'providing time services. [default: %(default)s]'
    )

    option = parser.parse_args()

    if option.daemon and not option.pid_file:
        return parser.error(
            'Running in daemon mode requires a PID file.')

    if option.log:
        log.startLogging(option.log)
    else:
        log.startLogging(sys.stdout)

    factory = PCIProtocolFactory(
        timesync=option.timesync,
        disable_clock=option.no_clock,
    )

    if option.serial_pci and option.tcp_pci:
        return parser.error('Both serial and TCP CBus PCI addresses were '
                            'specified!')
    elif option.serial_pci:
        SerialPort(factory.buildProtocol(), option.serial_pci, reactor,
                   baudrate=9600)
    elif option.tcp_pci:
        addr, port = option.tcp_pci.split(':', 2)
        point = TCP4ClientEndpoint(reactor, addr, int(port))
        point.connect(factory)
    else:
        return parser.error('No CBus PCI address was specified! (-s or -t '
                            'option)')

    mqtt_client = MqttClient(userdata=factory.protocol)
    mqtt_client.connect(option.broker_address, option.broker_port,
                        option.broker_keepalive)
    reactor.callLater(0, mqtt_client.loop_twisted)

    # TODO: replace this with twistd.
    if option.daemon:
        # this module is only needed if daemonising.
        from daemon import daemonize
        daemonize(option.pid_file)

    reactor.run()


if __name__ == '__main__':
    main()
