#! /usr/bin/python

# CLIENT

import os
import paramiko
import hashlib
import sys
import time
from socket import *
import argparse
import psutil
from datetime import datetime
from time import sleep
import errno

CLIENT_DAEMON_NAME = "client_thrput.py"
PORT_FILE = "/tmp/srv_thrput.port"
LOCAL_FILE = "./srv_thrput.py"
REMOTE_FILE = "/tmp/srv_thrput.py"

parser = argparse.ArgumentParser(usage="To run the program, you need two \
binary files:\n\rclient_thrput - client binary\n\rsrv_thrput - server \
binary\n\rThe server binary is automatically copied to the server and \
automatically launched on the server on port \"-port <PORT>\" (if \"-port \
<PORT>\" is not specified - random free port will be listen on server).\n\r\
The result is given to the log (if client is started with the \"-l <LOG>\" \
argument where <LOG> is name of the log file) or to the console (if \"-l\" \
is not specified).\n\rThe client sends \"-bytes <BYTES>\" bytes to server, \
then receives same bytes from server (if \"-bytes <BYTES>\" not set - default \
value 1024 will be used). The time is detected and the result is output in \
bytes per second.\n\r!!!To work, you need to open the port on the server \
using iptables or firewall-cmd!!!\n\rTo stop running client and server: \
./client_thrput -k <PID> ,where <PID> is client process.\n\rExample to get \
network throughput to log:\n\r./client_thrput.py -s 172.16.8.2 -u root -p \
password -l ./net_thrput.log -port 50044 -bytes 2048 -interval 60 - run test \
network throughput with sending 2048 bytes with interval 60 seconds, between \
this host and remote server 172.16.8.2 on port 50044 and write results to \
file ./net_thrput.log\n\rExample to get result to console with sending \
default 1024 bytes:\n\r./client_thrput.py -s 172.16.8.2 -u root -p password \
-port 50044\n\rExample to stop client and server:\n\r./client_thrput.py -k \
1033 - where \"1033\" is PID of client_thrput process\n\r")
parser.add_argument("-s", "--server", action="store",
                    help="remote server name or ip")
parser.add_argument("-u", "--user", action="store",
                    help="remote user name")
parser.add_argument("-p", "--password", action="store",
                    help="remote user password")
parser.add_argument("-l", "--log", action="store", help="path to log file")
parser.add_argument("-k", "--kill", action="store", help="kill daemon by pid")
parser.add_argument("-port", "--remote_port", action="store",
                    help="port listen on remote server, if you set 0 \
                    then port be random", default="0")
parser.add_argument("-bytes", "--bytes_buffer_size", action="store",
                    help="bytes to send and recieve, default is 1024",
                    default=1024)
parser.add_argument("-interval", "--interval_seconds", action="store",
                    help="interval in seconds to test network, default is 10",
                    default=10)

if len(sys.argv) < 3:
    parser.print_help(sys.stderr)
    sys.exit(1)

if len(sys.argv) == 3:
    args = parser.parse_args()
    pid_to_kill = args.kill
    if psutil.pid_exists(int(pid_to_kill)):
        process = psutil.Process(int(pid_to_kill))
        if process.name() in CLIENT_DAEMON_NAME:
            print "attempt to kill", process.name()
            process.kill()
        else:
            print "unable to kill not", CLIENT_DAEMON_NAME, "process"
    else:
        print CLIENT_DAEMON_NAME, "with pid", pid_to_kill, "does not exist"
    sys.exit(1)

args = parser.parse_args()

SERVER = args.server
USER = args.user
PASSWORD = args.password
LOG_FILE_NAME = args.log
REMOTE_PORT = args.remote_port
BUFFER_SIZE = int(args.bytes_buffer_size)
INTERVAL = int(args.interval_seconds)

if SERVER is None or USER is None or PASSWORD is None:
    print "SERVER, USER and PASSWORD is a mandatory arguments!"
    parser.print_help(sys.stderr)
    sys.exit(1)
# ------------------------------------------------------------


def copy_to_remote():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER, username=USER, password=PASSWORD)
    sftp = ssh.open_sftp()
    sftp.put(LOCAL_FILE, REMOTE_FILE)
    sftp.close()
    ssh.close()
# ------------------------------------------------------------


def set_remote_chown_to_root():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER, username=USER, password=PASSWORD)
    sftp = ssh.open_sftp()
    remote = sftp.file(REMOTE_FILE, 'r+')
    # set remote chown to root,root
    remote.chown(0, 0)
    sftp.close()
    ssh.close()
# ------------------------------------------------------------


def set_remote_chmod_to_execute():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER, username=USER, password=PASSWORD)
    sftp = ssh.open_sftp()
    remote = sftp.file(REMOTE_FILE, 'r+')
    # set remote chmod to 777
    remote.chmod(0777)
    sftp.close()
    ssh.close()
# ------------------------------------------------------------


def rexists(sftp, path):
    try:
        sftp.stat(path)
    except IOError, e:
        if e.errno == errno.ENOENT:
            return False
        raise
    else:
        return True
# ------------------------------------------------------------


def read_port_file():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER, username=USER, password=PASSWORD)
    sftp = ssh.open_sftp()
    remote = sftp.open(PORT_FILE)
    port = ""
    for i in remote:
        port += i
    sftp.close()
    ssh.close()
    return int(port)
# ------------------------------------------------------------


def check_remote_port():
    start_remote_server()
    p = read_port_file()
    s = socket(AF_INET, SOCK_STREAM)
    try:
        s.connect((SERVER, int(p)))
        s.shutdown(2)
        return True
    except:
        return False
# ------------------------------------------------------------


def start_remote_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER, username=USER, password=PASSWORD)
    # start remote server python script
    ssh.exec_command(REMOTE_FILE)[1]
    ssh.close()
# ------------------------------------------------------------


def get_remote_md5sum():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER, username=USER, password=PASSWORD)
    sftp = ssh.open_sftp()
    remote = sftp.file(REMOTE_FILE, 'r+')
    filehash = hashlib.md5()
    # get remote md5sum
    filehash.update(remote.read())
    sftp.close()
    ssh.close()
    return filehash.hexdigest()
# ------------------------------------------------------------


def rident():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER, username=USER, password=PASSWORD)
    sftp = ssh.open_sftp()
    if rexists(sftp, REMOTE_FILE):
        local_filehash = hashlib.md5()
        local_filehash.update(open(LOCAL_FILE).read())
        if (get_remote_md5sum()) == (local_filehash.hexdigest()):
            return "files_identical"
        else:
            return "files_not_identical"
    else:
        return "remote_file_not_exist"
    ssh.close()
# ------------------------------------------------------------


def save_port_file():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=SERVER, username=USER, password=PASSWORD)
    sftp = ssh.open_sftp()
    if rexists(sftp, PORT_FILE):
        sftp.remove(PORT_FILE)
    f = sftp.open(PORT_FILE, "w")
    f.write(str(REMOTE_PORT))
    sftp.close()
    ssh.close()
# ------------------------------------------------------------


def check_and_operate():
    if (rident()) == "files_not_identical" or (rident()) ==\
      "remote_file_not_exist":
        copy_to_remote()
        set_remote_chown_to_root()
        set_remote_chmod_to_execute()
    elif (rident()) == "files_identical":
        set_remote_chown_to_root()
        set_remote_chmod_to_execute()
# ------------------------------------------------------------


def get_netwrk_thrput():
    start_remote_server()
    server_port = read_port_file()
    send_data = 'x' * BUFFER_SIZE
    # create socket
    client = socket(AF_INET, SOCK_STREAM)
    # connect to server
    client.connect((SERVER, server_port))
    t1 = time.time()
    # send data to server
    client.send(send_data)
    # recieve same data from server
    recieve_data = client.recv(BUFFER_SIZE)
    t2 = time.time()
    # close connection
    client.close()
    # print result with bright green [1; ( normal green is [0; )
    print "Client connect to remote port", str(server_port),\
          "on server", str(SERVER)
    print "\033[1;32m\r", round((BUFFER_SIZE*2) / (t2-t1), 3),\
          "bytes/sec.", "\033[0;0m"
# ------------------------------------------------------------


def write_to_log(var, log_name):
    if not os.path.isfile(log_name):
        os.mknod(log_name)
    log = open(log_name, "a+")
    log.write(str(datetime.now())+" : "+str(var)+" bytes/sec.\r\n")
    log.close()
# ------------------------------------------------------------


def run_local_client_daemon():
    while not check_remote_port():
        sleep(1)
    else:
        start_remote_server()
        port = read_port_file()
        send_data = 'x' * BUFFER_SIZE
        client = socket(AF_INET, SOCK_STREAM)
        client.connect((SERVER, port))

        daemon_pid = os.fork()
        if daemon_pid == 0:
            # daemon action
            while True:
                t1 = time.time()
                client.send(send_data)
                recieve_data = client.recv(BUFFER_SIZE)
                t2 = time.time()
                thrput = round((BUFFER_SIZE*2) / (t2 - t1), 3)
                write_to_log(thrput, LOG_FILE_NAME)
                sleep(INTERVAL)
        else:
            print "Client (PID", daemon_pid, ") connect to remote port",\
                  str(read_port_file()), "on server", str(SERVER), "and start \
                  writing to log-file", LOG_FILE_NAME, "\nTo end writing log,\
                  terminate client and server run:",\
                  "./"+CLIENT_DAEMON_NAME, "-k", daemon_pid
        client.close()
# ------------------------------------------------------------
check_and_operate()
save_port_file()

if LOG_FILE_NAME is not None:
    run_local_client_daemon()
else:
    get_netwrk_thrput()
