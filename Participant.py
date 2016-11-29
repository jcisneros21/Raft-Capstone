from server import server
import random
import threading
from State import *
import RaftMessages_pb2 as protoc

class Participant:
  def __init__(self):
    self.termNumber = 0
    self.numNodes = 0

    self.server = server.server(self.handleMessage)
    self.server.start()

    self.state = FollowerState()
    self.timer = None
    self.initTimer()

  def isFollower(self):
    return isinstance(self.state, FollowerState)

  def isCandidate(self):
    return isinstance(self.state, CandidateState)

  def isLeader(self):
    return isinstance(self.state, LeaderState)

  def selectTimeout(self):
    return random.uniform(0.150, 0.300)

  def initTimer(self):
    self.electionTimeout = self.selectTimeout()
    self.timer = threading.Timer(self.electionTimeout, self.transition, [True,])
    self.timer.start()

  def transition(self, fromTimer=False):
    # if we have called transition and the election timer is still alive then we know
    # we heard from someone with a higher term number than us so immediately transition
    # to follower
    if self.isFollower():
      if fromTimer:
        self.state.stop()
        self.state = CandidateState()
        self.initTimer()
      else:
        self.state.stop()
        self.state = FollowerState()
        self.initTimer()
    elif self.isCandidate():
      if not fromTimer or self.state.heardFromLeader:
        self.state.stop()
        self.state = FollowerState()
        self.initTimer()
      elif self.state.votes > (self.numNodes / 2):
        self.state.stop()
        self.state = LeaderState()
      elif not self.state.heardFromLeader:
        self.state.stop()
        self.state = CandidateState()
        self.initTimer()
    elif self.isLeader():
      self.state.stop()
      self.state = FollowerState()
      self.initTimer()

  def handleMessage(self, incomingMessage):
    print("Handling message")
    servermessage = protoc.ServerMessage()
    servermessage.ParseFromString(incomingMessage)

    innermessage = None
    if servermessage.messageType == "RequestVote":
      innermessage = protoc.RequestVote()
      innermessage.ParseFromString(servermessage.serializedMessage)
    elif servermessage.messageType == "AppendEntries":
      innermessage = protoc.AppendEntries()
      innermessage.ParseFromString(servermessage.serializedMessage)

    if innermessage.termNumber > self.termNumber:
      self.termNumber = innermessage.termNumber
      self.transition()

    self.state.handleMessage(servermessage.messageType, servermessage.serializedMessage)

