/*
 * sageclient.js - Implementation of the saged websockets protocol in javascript
 * Copyright 2012 Michael Farrell <micolous+git@gmail.com>
 *
 * This library is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public License
 * along with this library.  If not, see <http://www.gnu.org/licenses/>.
 */
 
function delegate(that, thatMethod) { return function() { return thatMethod.apply(that, arguments); } }

var SageClient = (function() {
	var _uri;
	var _socket;
	
	function SageClient(uri) {
		_uri = uri;
	};
	
	SageClient.prototype.hasWebsockets = function() {
		return window.WebSocket != null || window.MozWebSocket != null;
	};
	
	SageClient.prototype.connect = function() {
		if (window.MozWebSocket != null) {
			// firefox <= 10.0
			_socket = new MozWebSocket(_uri);
		} else {
			_socket = new WebSocket(_uri);
		}
		
		_socket.onopen = delegate(this, this.onConnect);
		_socket.onclose = delegate(this, this.onDisconnect);
		_socket.onmessage = delegate(this, this.handleMessage);
	};
	
	SageClient.prototype.onConnect = function() {
		console.log('SageClient: Connected to server ' + _uri);
	};
	
	SageClient.prototype.onDisconnect = function(e) {
		console.log("SageClient: connection closed (" + e.code + ")");
	};
		
	SageClient.prototype.onLightingGroupOn = function(src, ga) {
		console.log('SageClient: Default onLightingGroupOn handler: src=' + src + ', ga=' + ga);
	};

	SageClient.prototype.onLightingGroupOff = function(src, ga) {
		console.log('SageClient: Default onLightingGroupOff handler: src=' + src + ', ga=' + ga);
	};

	SageClient.prototype.onLightingGroupRamp = function(src, ga, duration, level) {
		console.log('SageClient: Default onLightingGroupRamp handler: src=' + src+ ', ga=' + ga + ', duration=' + duration + ', level=' + level);
	};
	
	SageClient.prototype.onLightStates = function(states) {
		console.log('SageClient: Default onLightStates handler: ' + states);
	};
	
	SageClient.prototype.handleMessage = function(e) {
		msg = JSON.parse(e.data);
		//console.log('SageClient: message from server: cmd=' + msg.cmd + ', args=' + msg.args);

		console.log('SageClient: recieved server event: ' + msg.cmd + '(' + msg.args + ')');
		switch (msg.cmd) {
			case 'lighting_group_on':
				this.onLightingGroupOn(msg.args[0], msg.args[1]);
				break;

			case 'lighting_group_off':
				this.onLightingGroupOff(msg.args[0], msg.args[1]);
				break;

			case 'lighting_group_ramp':
				this.onLightingGroupRamp(msg.args[0], msg.args[1], msg.args[2], msg.args[3]);
				break;
			
			case 'light_states':
				this.onLightStates(msg.args[0]);
				break;

			default:
				console.log('SageClient: Unhandled event type!');
				break;
		}
		
	};
	
	SageClient.prototype._sendMessage = function(cmd, args) {
		m = JSON.stringify({cmd: cmd, args: args})
		_socket.send(m);
	};
	
	SageClient.prototype.lightingGroupOn = function(group_addrs) {
		this._sendMessage('lighting_group_on', [group_addrs]);
	};
	
	SageClient.prototype.lightingGroupOff = function(group_addrs) {
		this._sendMessage('lighting_group_off', [group_addrs]);
	};
	
	SageClient.prototype.lightingGroupRamp = function(group_addr, duration, level) {
		this._sendMessage('lighting_group_ramp', [group_addr, duration, level]);
	};
	
	SageClient.prototype.lightingGroupTerminateRamp = function(group_addr) {
		this._sendMessage('lighting_group_terminate_ramp', [group_addr]);
	};
	
	SageClient.prototype.getLightStates = function(group_addrs) {
		this._sendMessage('get_light_states', group_addrs);
	};
	
	return SageClient;
})();
	
