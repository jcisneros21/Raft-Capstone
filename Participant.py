from server import server
import random
import threading
from State import *
import RaftMessages_pb2 as protoc
import os

class Participant:
  def __init__(self):
    self.termNumber = 0

    self.server = server.server(self.handleMessage)
    self.server.start()

    self.numNodes = len(self.server.nodeaddrs) + 1

    self.state = FollowerState(0, self.server)
    self.timer = None
    self.initTimer()

  def isFollower(self):
    return isinstance(self.state, FollowerState)

  def isCandidate(self):
    return isinstance(self.state, CandidateState)

  def isLeader(self):
    return isinstance(self.state, LeaderState)

  def selectTimeout(self):
    return random.uniform(5,10)

  def initTimer(self):
    self.electionTimeout = self.selectTimeout()
    self.timer = threading.Timer(self.electionTimeout, self.transition, [True,])
    self.timer.start()

  def transition(self, fromTimer=False):
    #self.termNumber += 1
    self.timer.cancel()
    # if we have called transition and the election timer is still alive then we know
    # we heard from someone with a higher term number than us so immediately transition
    # to follower
    if self.isFollower():
      if fromTimer:
        print("Follower transitions into Candidate")
        self.termNumber += 1
        self.state.stop()
        self.state = CandidateState(self.termNumber, self.server)
        self.initTimer()
      else:
        print("Follower transitions into Follower")
        self.state.stop()
        self.state = FollowerState(self.termNumber, self.server)
        self.initTimer()
    elif self.isCandidate():
      #print("We have {} votes".format(self.state.votes))
      if self.state.heardFromLeader and not fromTimer:
        print("Candidate transitions into Follower")
        self.state.stop()
        self.state = FollowerState(self.termNumber, self.server)
        self.initTimer()
      elif self.state.votes > (self.numNodes / 2):
        print("Candidate transitions into Leader")
        #self.termNumber += 1
        self.state.stop()
        self.state = LeaderState(self.termNumber, self.server)
      elif not self.state.heardFromLeader:
        print("Candidate transitions into Candidate")
        self.state.stop()
        self.state = CandidateState(self.termNumber, self.server)
        self.initTimer()
    elif self.isLeader():
      print("Leader transitions into Follower")
      self.state.stop()
      self.state = FollowerState(self.termNumber, self.server)
      self.initTimer()

  def handleMessage(self, incomingMessage):
    servermessage = protoc.WrapperMessage()
    servermessage.ParseFromString(incomingMessage)
    i = 0
 
    if self.isCandidate():
      print("I am Candidate")
    elif self.isFollower():
      print("I am Follower")
    elif self.isLeader():
      print("I am Leader")

    innermessage = None
    #print(servermessage.type)
    #print()
    if servermessage.type == protoc.REQUESTVOTE:
      print("Recieved RequestVote MSG from ",end="")
      innermessage = protoc.RequestVote()
      innermessage = servermessage.rvm
    elif servermessage.type == protoc.VOTERESULT:
      print("Recieved VoteResult MSG from ",end="")
      innermessage = protoc.VoteResult()
      innermessage = servermessage.vrm
    elif servermessage.type == protoc.APPENDENTRIES:
      print("Revieved AppendEntries MSG from ",end="")
      innermessage = protoc.AppendEntries()
      innermessage = servermessage.aem
    elif servermessage.type == protoc.APPENDREPLY:
      print("Recieved AppendReply MSG from ",end="")
      innermessage = protoc.AppendReply()
      innermessage = servermessage.arm

    print(innermessage.fromAddr)
    if innermessage.term > self.termNumber:
      self.termNumber = innermessage.term
      #self.transition()

    self.state.handleMessage(servermessage.type, innermessage, self.termNumber)
    
    if self.isCandidate():
      if self.state.votes > (self.numNodes / 2):
        self.transition()
      elif self.state.heardFromLeader:
        self.transition()
        self.state.heardFromLeader = False
    elif self.isFollower():
      if self.state.heardFromLeader:
        self.timer.cancel()
        self.initTimer()
        self.state.heardFromLeader = False
