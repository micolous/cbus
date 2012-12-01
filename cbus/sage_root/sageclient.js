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

var SageClient = (function() {
	var _uri;
	var _socket;
	
	function SageClient(uri) {
		_uri = uri;
	};
	
	SageClient.prototype.connect = function() {
		_socket = new WebSocket(_uri);
		
		_socket.onopen = this.onConnect;
		
		_socket.onclose = function(e) {
			console.log("connection closed (" + e.code + ")");
		};
		
		_socket.onmessage = this.handleMessage;
	};
	
	SageClient.prototype.onConnect = function() {
		console.log('SageClient: Connected to server ' + _uri);
	};
	
	SageClient.prototype.handleMessage = function(e) {
		msg = JSON.parse(e.data);
		console.log('message from server: cmd=' + msg.cmd + ', args=' + msg.args);
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
	
	return SageClient;
})();
	