# Network-throughput-between-two-hosts
To run the program, you need two files:<br/>
client_thrput.py - client<br/>
srv_thrput.py - server<br/>
The server is automatically copied to the server and automatically launched on the server on port \"-port [PORT]\" (if \"-port <PORT>\" is not specified - random free port will be listen on server).<br/>
The result is given to the log (if client is started with the \"-l <LOG>\" argument where <LOG> is name of the log file) or to the console (if \"-l\" is not specified).<br/>
The client sends \"-bytes <BYTES>\" bytes to server, then receives same bytes from server (if \"-bytes <BYTES>\" not set - default value 1024 will be used).<br/>
The time is detected and the result is output in bytes per second.<br/>
!!!To work, you need to open the port on the server using iptables or firewall-cmd!!!<br/>
To stop running client and server: ./client_thrput -k <PID> ,where <PID> is client process.<br/>
Example to get network throughput to log:<br/>
./client_thrput.py -s 172.16.8.2 -u root -p password -l ./net_thrput.log -port 50044 -bytes 2048 -interval 60 - run test network throughput with sending 2048 bytes with interval 60 seconds, between this host and remote server 172.16.8.2 on port 50044 and write results to file ./net_thrput.log<br/>
Example to get result to console with sending default 1024 bytes:<br/>
./client_thrput.py -s 172.16.8.2 -u root -p password -port 50044<br/>
Example to stop client and server:<br/>
./client_thrput.py -k 1033 - where \"1033\" is PID of client_thrput process<br/>
