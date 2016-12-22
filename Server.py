import threading
import socket
import RaftMessages_pb2 as protoc
import sys
import subprocess
import re
import State

class Server:
    def __init__(self):
        self.nodeaddrs = []
        self.StateInfo = State(State.Follower)

        # figure out who we need to listen for
        nodeaddrsfile = open('nodeaddrs.txt', 'r')

        for line in nodeaddrsfile:
            hostaddr = line.split(',')[0]
            socketnum = int(line.split(',')[1].strip('\n'))

            # if we just read our own address from the file
            if hostaddr = self.__getownip():
                self.addr = (hostaddr, socketnum)
            else:
                self.nodeaddrs.append((hostaddr, socketnum))

        nodeaddrsfile.close()

    def __listen(self):
        listenSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listenSocket.bind(self.addr)
        while True:
            data = listenSocket.recv(1024)

    def __getownip(self):
        result = subprocess.check_output(['ifconfig'], universal_newlines=True)
        ips = re.findall('10\.0\.0\.[0-9]{1,3}', result)
        return ips[0]

    def handleMessage(self, messageData):
        # first thing we do is parse the message data
        outerMessage = protoc.WrapperMessage()
        outerMessage.ParseFromString(messageData)

        if outerMessage.type == protoc.REQUESTVOTE:
            innerMessage = protoc.RequestVote()
            innerMessage = outerMessage.rvm
        elif outerMessage.type == protoc.VOTERESULT:
            innerMessage = protoc.VoteResult()
            innerMessage = outerMessage.vrm
        elif outerMessage.type == protoc.APPENDENTRIES:
            innerMessage = protoc.AppendEntries()
            innerMessage = outerMessage.aem
        elif outerMessage.type == protoc.APPENDREPLY:
            innerMessage = protoc.AppendReply()
            innerMessage = outerMessage.arm

        # for all servers in all states the first thing we need to check is
        # that our term number is not out of date
        if innerMessage.term > self.StateInfo.term:
            self.StateInfo = State(State.Follower, innerMessage.term)
            return

        # if the term number is valid, the normal rules for the current state
        # apply
        if ()
