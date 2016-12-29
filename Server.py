import threading
import socket
import RaftMessages_pb2 as protoc
import sys
import subprocess
import re
import State
import random

class Server:
    def __init__(self):
        self.nodeaddrs = []
        self.Socket = None

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

        self.StateInfo = State.FollowerState()

        # init election timer
        self.electionTimeout = random.uniform(1, 5)
        self.timer = threading.Timer(self.electionTimeout, self.transition, [True,])

    def listen(self):
        self.Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.Socket.bind(self.addr)
        while True:
            data = self.Socket.recv(1024)
            # threading stuff


    def getownip(self):
        result = subprocess.check_output(['ifconfig'], universal_newlines=True)
        ips = re.findall('10\.0\.0\.[0-9]{1,3}', result)
        return ips[0]

    def isFollower(self):
        return isinstance(self.StateInfo, State.FollowerState)

    def isCandidate(self):
        return isinstance(self.StateInfo, State.CandidateState)

    def isLeader(self):
        return isinstance(self.StateInfo, State.LeaderState)

    def sendMessage(self, messageType, message):
        outgoingMessage = protoc.WrapperMessage()
        outgoingMessage.type = messageType

        if messageType == protoc.REQUESTVOTE:
            outgoingMessage.rvm.CopyFrom(message)
        elif messageType == protoc.VOTERESULT:
            outgoingMessage.vrm.CopyFrom(message)
        elif messageType == protoc.APPENDENTRIES:
            outgoingMessage.aem.CopyFrom(message)
        elif messageType == protoc.APPENDREPLY:
            outgoingMessage.arm.CopyFrom(message)

        self.Socket.sendto(outgoingMessage.SerializeToString(), (message.toAddr, message.toPort))

    def messgeHandler(self, messageData):
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
            # transition to follower
            return
        #TODO: Check if commitindex > last applied after we implement logs

        # if the term number is valid, the normal rules for the current state
        # apply
        replyMessageType, replyMessage = self.StateInfo.handleMessage(messageType, message, termNumber)
        self.sendMessage(replyMessageType, replyMessage)
