import threading
import socket
import RaftMessages_pb2 as protoc
import sys
import subprocess
import re
import State
import random
import math
import queue
import os

class Server:
    def __init__(self):
        self.NodeAddrs = []
        self.nextAdded = None
        self.addr = None 
        self.Socket = None
        self.logFileName = None
        self.ServerFlag = False
        self.TimerFlag = True
        
        self.foundLeader = False

        # figure out who we need to listen for
        nodeaddrsfile = open('nodeaddrs.txt', 'r')

        for line in nodeaddrsfile:
            hostaddr = line.split(',')[0]
            socketnum = int(line.split(',')[1].strip('\n'))

            # if we just read our own address from the file
            if hostaddr == self.getownip():
                self.addr = (hostaddr, socketnum)
                self.logFileName = line.split(',')[2].strip()
                print("My address is {} and my logfile is {}\n".format(self.addr, self.logFileName))
            else:
                self.NodeAddrs.append((hostaddr, socketnum))

        # If IP address is not found in file, create a temp port number
        if self.addr is None:
            self.addr = (self.getownip(), 8999)
            print(self.addr)

        nodeaddrsfile.close()

        self.StateSemaphore = threading.Semaphore()
        self.StateInfo = State.FollowerState(0, self.logFileName)

        self.outgoingMessageQ = queue.Queue()
        # start message queue handling thread
        self.queueThread = threading.Thread(target=self.sendMessageThread)
        self.queueThread.start()

        # start up client listener thread
        self.clientListener = threading.Thread(target=self.clientListenerThread)
        self.clientListener.start()

        # init election timer and transition to CandidateState if it runs out
        self.electionTimeout = random.uniform(8, 10)
        print("Election Timeout Value: {}\n".format(self.electionTimeout))
        self.timer = threading.Timer(self.electionTimeout, self.transition, ('Candidate',))
        
        # If we have an IP address and Port Number, start the timer.
        if self.addr[1] is not 8999:
            self.timer.start()
            
        self.heartbeatTimeout = 5
        self.listen()

    # Need to find Leader
    # TO-DO: Modfify it to find leader
    def sendJoinMessages(self):
        for server in self.NodeAddrs:
            messageType, message = self.StateInfo.joinSystemMessage()
            message.toAddr = server[0]
            message.toPort = server[1]
            self.outgoingMessageQ.put_nowait((messageType, message))

    def sendJoinMessage(self, addr, port):
        messageType, message = self.StateInfo.joinSystemMessage()
        message.toAddr = addr
        message.toPort = port
        self.outgoingMessageQ.put_nowait((messageType, message))

    # Add new host to host file
    def writeHostToFile(self, address, port):
        with open('nodeaddrs.txt', 'a') as addrFile:
            logNumber = self.getLogNumber(address)
            addrFile.write(address + ',' + str(port) + ',' + 'logfile' + logNumber + '.txt\n')

    # Add new host to host list
    def addHostToNodeAddrs(self, address, port):
        print(address)
        print(port)
        self.NodeAddrs.append((address, port))
    
    def addHostInfo(self, address, port): 
        self.addr = (address, port)
        logNumber = self.getLogNumber(address)
        self.logFileName = "logfile" + logNumber + ".txt"
        print(self.logFileName)
        self.timer.start()
        self.listen()
   
    # Get new Port for Host
    def getNewPort(self):
        return (len(self.NodeAddrs) + 9000 + 1)

    def getLogNumber(self, addr):
        parts = addr.split('.')
        return parts[3]

    def extractNetworkInfo(self, data):
        addr = ""
        port = 0
        i = 0
        for string in data.split():
            i += 1
            if i == 3:
                addr = string.strip(',')
            if i == 4:
                port = int(string)
        return addr, port

    def sendJoinReplyMessage(self, address, port):
        messageType, message = self.StateInfo.createJoinReply()
        message.fromAddr = self.addr[0]
        message.fromPort = self.addr[1]
        message.toAddr = address
        message.toPort = 8999
        message.success = True
        message.assignedAddr = address
        message.assignedPort = port
        self.outgoingMessageQ.put_nowait((messageType, message))

    # def extractNetworkFromFile(self):
        

    # Send AppendHost Messages to all Followers
    # def sendAppendHostMessages(self, appendHostMessage, messageType, port):
        #for server in self.NodeAddrs:
            #appendHostMessage.toAddr = server[0]
            #appendHostMessage.toPort = server[1]
            #appendHostMessage.hostPort = port
            #self.outgoingMessageQ.put_nowait((messageType, appendHostMessage))  

    def listen(self):
        self.Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.Socket.bind(self.addr)
        if self.addr[1] == 8999:
            print("HEEEEEEEEEELLLO")
            self.sendJoinMessages()
        while True:
            data = self.Socket.recv(1024)
            threading.Thread(target=self.messageHandler, args=(data,)).start()

    def selectElectionTimeoutValue(self):
        self.electionTimeout = random.uniform(8, 10)

    def resetTimer(self):
        self.timer.cancel()
        self.selectElectionTimeoutValue()
        if self.TimerFlag:
            print("Election Timeout Value: {}\n".format(self.electionTimeout))
        self.timer = threading.Timer(self.electionTimeout, self.transition, ['Candidate',])
        self.timer.start()

    def getownip(self):
        result = subprocess.check_output(['ifconfig'], universal_newlines=True)
        ips = re.findall('10\.0\.0\.[0-9]{1,3}', result)
        return ips[0]

    def requestVotes(self):
        for server in self.NodeAddrs:
            messageType,message = self.StateInfo.requestVote()
            message.toAddr = server[0]
            message.toPort = server[1]
            self.outgoingMessageQ.put_nowait((messageType, message))

    def heartbeat(self):
        for server in self.NodeAddrs:
            messageType,message = self.StateInfo.createAppendEntries(server[0], server[1])
            self.outgoingMessageQ.put_nowait((messageType, message))
        self.timer = threading.Timer(self.heartbeatTimeout, self.heartbeat)
        self.timer.start()

    def transition(self, state):
        successfulTransition = False
        if self.StateSemaphore.acquire(blocking=False):
            savedLog = self.StateInfo.log
            if self.ServerFlag:
                print('Transitioning to ' + state)
            self.timer.cancel()
            if state == 'Follower':
                self.StateInfo = State.FollowerState(self.StateInfo.term, self.logFileName, savedLog)
                # init new election timer
                self.resetTimer()
            elif state == 'Candidate':
                self.StateInfo = State.CandidateState(self.StateInfo.term + 1, self.logFileName, savedLog)
                self.resetTimer()
                self.requestVotes()
            elif state == 'Leader':
                self.StateInfo = State.LeaderState(self.StateInfo.term, self.NodeAddrs, self.logFileName, savedLog)
                self.heartbeat()
            self.StateSemaphore.release()
            successfulTransition = True
        return successfulTransition

    def isFollower(self):
        return isinstance(self.StateInfo, State.FollowerState)

    def isCandidate(self):
        return isinstance(self.StateInfo, State.CandidateState)

    def isLeader(self):
        return isinstance(self.StateInfo, State.LeaderState)

    def sendMessageThread(self):
        while True:
            messageTuple = self.outgoingMessageQ.get()
            if self.ServerFlag:
                print(str(messageTuple[1]))
                print('Sending {} message'.format(messageTuple[0]))
            messageTuple[1].fromAddr = self.addr[0]
            messageTuple[1].fromPort = self.addr[1]
            outgoingMessage = protoc.WrapperMessage()
            outgoingMessage.type = messageTuple[0]

            if messageTuple[0] == protoc.REQUESTVOTE:
                outgoingMessage.rvm.CopyFrom(messageTuple[1])
            elif messageTuple[0] == protoc.VOTERESULT:
                outgoingMessage.vrm.CopyFrom(messageTuple[1])
            elif messageTuple[0] == protoc.APPENDENTRIES:
                outgoingMessage.aem.CopyFrom(messageTuple[1])
            elif messageTuple[0] == protoc.APPENDREPLY:
                outgoingMessage.arm.CopyFrom(messageTuple[1])
            elif messageTuple[0] == protoc.JOINSYSTEM:
                outgoingMessage.js.CopyFrom(messageTuple[1])
            elif messageTuple[0] == protoc.JOINREPLY:
                outgoingMessage.jr.CopyFrom(messageTuple[1])
            #elif messageTuple[0] == protoc.APPENDHOST:
                #outgoingMessage.ah.CopyFrom(messageTuple[1])
            #elif messageTuple[0] == protoc.APPENDHOSTREPLY:
                #outgoingMessage.ahr.CopyFrom(messageTuple[1])
            
            if self.addr[1] is 8999:
                print("HEEELLLLLLLLLLOOOOOOOO")
            self.Socket.sendto(outgoingMessage.SerializeToString(), (messageTuple[1].toAddr, messageTuple[1].toPort))

    def messageHandler(self, messageData):
        # first thing we do is parse the message data
        outerMessage = protoc.WrapperMessage()
        outerMessage.ParseFromString(messageData)

        if outerMessage.type == protoc.REQUESTVOTE:
            innerMessage = protoc.RequestVote()
            innerMessage = outerMessage.rvm
            messageType = protoc.REQUESTVOTE
        elif outerMessage.type == protoc.VOTERESULT:
            innerMessage = protoc.VoteResult()
            innerMessage = outerMessage.vrm
            messageType = protoc.VOTERESULT
        elif outerMessage.type == protoc.APPENDENTRIES:
            innerMessage = protoc.AppendEntries()
            innerMessage = outerMessage.aem
            messageType = protoc.APPENDENTRIES
        elif outerMessage.type == protoc.APPENDREPLY:
            innerMessage = protoc.AppendReply()
            innerMessage = outerMessage.arm
            messageType = protoc.APPENDREPLY

        elif outerMessage.type == protoc.JOINSYSTEM:
            innerMessage = protoc.JoinSystem()
            innerMessage = outerMessage.js
            messageType = protoc.JOINSYSTEM
        elif outerMessage.type == protoc.JOINREPLY:
            innerMessage = protoc.JoinReply()
            innerMessage = outerMessage.jr
            messageType = protoc.JOINREPLY
        #elif outerMessage.type == protoc.APPENDHOST:
            #innerMessage = protoc.AppendHost()
            #innerMessage = outerMessage.ah
            #messageType = protoc.APPENDHOST
        #elif outerMessage.type == protoc.APPENDHOSTREPLY:
            #innerMessage = protoc.AppendHostReply()
            #innerMessage = outerMessage.ahr
            #messageType = protoc.APPENDHOSTREPLY
        
        # Until the instance of Raft has a log file
        if messageType != protoc.JOINREPLY and self.logFileName is None:
            return None 
   
        if messageType == protoc.JOINREPLY:
            print("ADDING HOST")

        # for all servers in all states the first thing we need to check is
        # that our term number is not out of date

        # Only check the messages that contain term numbers
        termMessages = [0,1,2,3,5]
        if messageType in termMessages:
            if innerMessage.term > self.StateInfo.term:
                if self.ServerFlag:
                    print('Got a higher term number\n\n')
                self.StateInfo.term = innerMessage.term
                self.transition('Follower')

        # if the term number is valid, the normal rules for the current state
        # apply
        replyMessageType, replyMessage = self.StateInfo.handleMessage(messageType, innerMessage)
        
        #TO-DO: Allow host to be added even when it is the zero entry in log
        #TO-DO: Make function to add all entries of host to nodeAddr when accepted to System
        #       (Recover process)
        #TO-DO: Should I restart nodeaddr when starting up? Prop huh.
        #TO-DO:: Allow for hosts to leave the system
        if self.isFollower():
            # only responsibility is to respond to messages from Candidates and leaders
            if replyMessageType == protoc.APPENDREPLY and replyMessage.success:
                self.resetTimer()
            if replyMessageType == protoc.JOINREPLY and replyMessage.success == False:
                replyMessage.toAddr = innerMessage.fromAddr
                replyMessage.toPort = innerMessage.fromPort
            if messageType == protoc.JOINREPLY and innerMessage.success:
                self.addHostInfo(innerMessage.assignedAddr, innerMessage.assignedPort)
            
            if self.StateInfo.leaderInfo != None and self.foundLeader == False:
                self.foundLeader = True
                if self.StateInfo.leaderInfo not in self.NodeAddrs:
                    print("\n\nWe are contacting another leader\n\n")
                    self.sendJoinMessage(self.StateInfo.leaderInfo[0], selfStateInfo.leaderInfo[1])
 
            #if replyMessageType == protoc.APPENDHOSTREPLY and replyMessage.success:
                # Uncomment when using the raspberry pi
                #self.writeHostToFile(innerMessage.hostAddr, innerMessage.hostPort)
                #self.addHostToNodeAddrs(innerMessage.hostAddr, innerMessage.hostPort)
                #replyMessage.success = True
            searchIndex = self.StateInfo.searchLastAddedHost()
            if searchIndex > self.StateInfo.lastAppliedHost:
                self.StateInfo.lastAppliedHost = self.StateInfo.searchLastAddedHost()
                data = self.StateInfo.retrieveLogData(self.StateInfo.lastAppliedHost)
                address, port = self.extractNetworkInfo(data)
                # self.writeHostToFile(address, port)
                if address is not self.addr[0]:
                    self.addHostToNodeAddrs(address, port)
            
            if replyMessageType is not None:
                self.outgoingMessageQ.put_nowait((replyMessageType, replyMessage))
        elif self.isCandidate():
            # if we have something to send then just need to send it
            if replyMessageType is not None:
                self.outgoingMessageQ.put_nowait((replyMessageType, replyMessage))
            else:
                # otherwise we got a vote result or a heartbeat
                if self.StateInfo.heardFromLeader:
                    # if heartbeat someone else won
                    self.transition('Follower')
                elif self.StateInfo.votes > (len(self.NodeAddrs) + 1) // 2:
                    # if vote, check to see if we won
                    self.transition('Leader')

        elif self.isLeader():
            if self.StateInfo.searchLastAddedHost() > self.StateInfo.lastAppliedHost:
                self.StateInfo.lastAppliedHost = self.StateInfo.searchLastAddedHost()
                data = self.StateInfo.retrieveLogData(self.StateInfo.lastAppliedHost)
                address, port = self.extractNetworkInfo(data)
                self.writeHostToFile(address, port)
                self.addHostToNodeAddrs(address, port)
                self.StateInfo.addHostToFollowerIndex(address)
                print("Sent Reply")
                self.sendJoinReplyMessage(address, port)
            #if replyMessageType == protoc.APPENDHOST:
                #hostPort = self.getNewPort()
                #self.nextAdded = (replyMessage.hostAddr, hostPort)
                #self.sendAppendHostMessages(replyMessage, replyMessageType, hostPort)
            if messageType == protoc.JOINSYSTEM:
                addHostData = "Add Host: " + innerMessage.fromAddr + ", " + str(self.getNewPort())
                print("This is data: " + addHostData)
                messageType,logEntryMessage = self.StateInfo.createLogEntry(addHostData)
                for server in self.NodeAddrs:
                    messageType,outgoingMessage = self.StateInfo.createAppendEntries(server[0], server[1], [logEntryMessage,])
                    self.outgoingMessageQ.put_nowait((messageType, outgoingMessage))
            elif replyMessageType is not None:
                replyMessage.toAddr = innerMessage.fromAddr
                replyMessage.toPort = innerMessage.fromPort
                self.outgoingMessageQ.put_nowait((replyMessageType, replyMessage))
            #else:00
                #if self.StateInfo.appended > (len(self.NodeAddrs) + 1) // 2:
                    #self.StateInfo.appended = 0
                    #self.writeHostToFile(innerMessage.hostAddr, innerMessage.hostPort)
                    #self.writeToNodeAddrs(innerMessage.hostAddr, innerMessage.hostPort)
                    

    def clientListenerThread(self):
        while True:
            clientCommand = sys.stdin.readline()
            print()
            if clientCommand.strip() == 'printlog':
                self.StateInfo.printLog()
            elif clientCommand.strip() == 'quit':
                os._exit(1)
            elif clientCommand.strip() == '-s':
                if self.ServerFlag:
                    self.ServerFlag = False
                else:
                    self.ServerFlag = True
            elif clientCommand.strip() == '-timer':
                if self.TimerFlag:
                    self.TimerFlag = False
                else:
                    self.TimerFlag = True
            elif clientCommand.strip() == '-clear':
                for i in range(0,40):
                    print()
            elif self.isLeader():
                messageType,logEntryMessage = self.StateInfo.createLogEntry(clientCommand.strip())
                for server in self.NodeAddrs:
                    messageType,outgoingMessage = self.StateInfo.createAppendEntries(server[0], server[1], [logEntryMessage,])
                    self.outgoingMessageQ.put_nowait((messageType, outgoingMessage))
