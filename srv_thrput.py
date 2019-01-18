#! /usr/bin/python

# SERVER

import os
import sys
import time
from socket import *

PORT_FILE = "/tmp/srv_thrput.port"
# ----------------------------------------


def get_port():
    f = open(PORT_FILE, "r")
    port = f.read()
    return int(port)
# ----------------------------------------


def overwrite_port(port):
    if os.path.isfile(PORT_FILE):
        os.remove(PORT_FILE)
    os.mknod(PORT_FILE)
    f = open(PORT_FILE, "w")
    f.write(str(port))
    f.close()
# ----------------------------------------


# set size of buffer to 1024 bytes (or 1 kilobyte)
BUFSIZE = 1024
# create socket
s = socket(AF_INET, SOCK_STREAM)
# bind socket to port
s.bind(('', get_port()))
# get port number (this need if port set to "0" - random port)
addr_server, port_server = s.getsockname()
# if port set to "0" then overwrite PORT_FILE with current random port number
if get_port() == 0:
    overwrite_port(port_server)
# listen incoming connection
s.listen(1)
# recieve data from client side
# ----------------------------------------
conn, addr_client = s.accept()
while conn:
    data = conn.recv(BUFSIZE)
    if not data:
        break
# send same data to client
    conn.send(data)
# ----------------------------------------
conn.close()
