import threading
import socket
import RaftMessages_pb2 as protoc
import sys
import subprocess
import re

class server:
    def __init__(self, callback, port):
        self.nodeaddrs = []

        # figure out who we need to listen for
        nodeaddrsfile = open('nodeaddrs.txt', 'r')

        for line in nodeaddrsfile:
            hostaddr = line.split(',')[0]
            socketnum = int(line.split(',')[1].strip('\n'))
            #if hostaddr == self.getownip():
            self.addr = ("0.0.0.0", port)
            #else:
            if socketnum != port:
                self.nodeaddrs.append(('0.0.0.0', socketnum))

        nodeaddrsfile.close()
        self.listenThread = None
        self.socket = None
        self.participantCallback = callback

    def start(self):
        self.listenThread = threading.Thread(None, self.listen)
        print("Starting listen thread.")
        self.listenThread.start()
        # start listening for them
        """
        listensocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listensocket.settimeout(timeout)
        listensocket.bind(self.addr)
        try:
            data = listensocket.recv(1024)
            # if we get here then we heard from someone who won the election
            heartbeat = protoc.HeartbeatTest()
            heartbeat.ParseFromString(data)
            print(heartbeat)
        except:
            # if we get here then the socket timed out and we have won the election
            for node in self.nodeaddrs:
                temp = protoc.HeartbeatTest()
                temp.fromnode = self.addr[0]
                temp.tonode = node[0]
                temp.message = 'I win!!'
                listensocket.sendto(temp.SerializeToString(), node)
                print("I win!")
        """

    def listen(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(self.addr)
        print("Listening on {}".format(self.addr))
        while True:
            print("In listen")
            data = self.socket.recv(1024)
            print("Got something!!")
            print(data)
            self.participantCallback(data)

    def talk(self, messageType, message):
        message.fromNode.append(self.addr[0])
        message.fromNode.append(str(self.addr[1]))
        messagetosend = protoc.WrapperMessage()
        messagetosend.messageType = messageType
        if messageType == "RequestVote":
          for server in self.nodeaddrs:
            message.toNode.append(server[0])
            message.toNode.append(str(server[1]))
            messagetosend.serializedMessage = message.SerializeToString()
            #print("Sending:")
            #print(message)
            #print()
            sent = self.socket.sendto(messagetosend.SerializeToString(), (message.toNode[0], int(message.toNode[1])))
            print("sendto returned {}".format(sent))
        return
        messagetosend.serializedMessage = message.SerializeToString()
        self.socket.sendto(messagetosend.SerializeToString(), (message.toNode[0], int(message.toNode[1])))
            
    def getownip(self):
        result = subprocess.check_output(['ifconfig'], universal_newlines=True)
        ips = re.findall('inet[ addr]*[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', result)
        #print(ips[0][5:14])
        return ips[0][5:14]
        #for i in range(len(ips)):
        #    if ips[i][10:12] == '10':
        #        return ips[i][10:]

#test = server()
# for now this argument is the election timeout
#test.start(int(sys.argv[1]))

