import threading
import socket
import RaftMessages_pb2 as protoc
import sys
import subprocess
import re

class server:
    def __init__(self, callback):
        self.nodeaddrs = []

        # figure out who we need to listen for
        nodeaddrsfile = open('nodeaddrs.txt', 'r')

        for line in nodeaddrsfile:
            hostaddr = line.split(',')[0]
            socketnum = int(line.split(',')[1].strip('\n'))
            if hostaddr == self.getownip():
                self.addr = (hostaddr, socketnum)
            else:
                self.nodeaddrs.append((hostaddr, socketnum))

        nodeaddrsfile.close()
        self.listenThread = None
        self.socket = None
        self.participantCallback = callback

    def start(self):
        self.listenThread = threading.Thread(None, self.listen)
        self.listenThread.start()
       
    def listen(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(self.addr)
        while True:
            data = self.socket.recv(1024)
            self.participantCallback(data)

    def talk(self, messageType, message):
        message.fromAddr = self.addr[0]
        message.fromPort = self.addr[1]
        messagetosend = protoc.WrapperMessage()
        messagetosend.type = messageType
        if messageType == protoc.REQUESTVOTE:
          for server in self.nodeaddrs:
            message.toAddr = server[0]
            message.toPort = server[1]
            messagetosend.rvm.CopyFrom(message)
            self.socket.sendto(messagetosend.SerializeToString(), (message.toAddr, message.toPort))
          return
        elif messageType == protoc.APPENDENTRIES:
          for server in self.nodeaddrs:
            message.toAddr = server[0]
            message.toPort = server[1]
            messagetosend.aem.CopyFrom(message)
            self.socket.sendto(messagetosend.SerializeToString(), (message.toAddr, message.toPort))
          return
        elif messageType == protoc.VOTERESULT:
            messagetosend.vrm.CopyFrom(message)

        self.socket.sendto(messagetosend.SerializeToString(), (message.toAddr, message.toPort))
            
    def getownip(self):
        result = subprocess.check_output(['ifconfig'], universal_newlines=True)
        ips = re.findall('10\.0\.0\.[0-9]{1,3}', result)
        return ips[0]
        
