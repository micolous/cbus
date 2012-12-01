import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('172.26.1.80', 8888))
#s.send('<policy-file-request/>\0')
s.send('<cbus_auth_cmd  value="0x22284440" cbc_version="3.7.0" count="0" />\0')

#<project-file-request /><skin-file-request />\0')

while 1:
	r = s.recv(1024)
	if r:
		print r
	
