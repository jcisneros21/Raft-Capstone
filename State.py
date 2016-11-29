import server
import RaftMessages_pb2 as protoc

class State():
  def __init__(self):
    self.servercallback = server.server.talk
  
  def sendVoteNACK(self, toNode, termNumber):
    voteack = protoc.VoteResult()
    voteack.toNode = toNode
    voteack.term = termNumber
    voteack.granted = False
    servercallback(voteack)

  def sendVoteACK(self, toNode, termNumber):
    voteack = protoc.VoteResult()
    voteack.toNode = toNode
    voteack.term = termNumber
    voteack.granted = True
    servercallback("VoteResult", voteack)

class LeaderState(State):
  def __init__(self):
    State.__init__()
    print("Leader")
    
  #def appendEntries():

  def stop(self):
    print("Stopping leader state.")

class CandidateState(State):
  def __init__(self):
    State.__init__()
    print("Candidate")
    self.votes = 0
    self.heardFromLeader = False

  def stop(self):
    print("Stopping candidate state.")

  def handleMessage(self, messageType, message, termNumber):
    message = None
    if messageType == "RequestVote":
      message = protoc.RequestVote()
      message.ParseFromString(message)
      sendVoteNACK(message.fromNode, termNumber)
    elif messageType == "AppendEntries":
      #TODO: implement this
      pass
    elif messageType == "VoteResult":
      message = protoc.VoteResult()
      message.ParseFromString(message)
      if message.granted:
        votes += 1

  #def requestVotes():
    #for server in self.nodeaddrs:
      #message = RequestVote_pb2.RequestVote()
      #OutQueue.put_nowait(RequestVote_pb2)

class FollowerState(State):
  def __init__(self):
    State.__init__()
    print("Follower")
    self.voted = False

  def stop(self):
    print("Stopping follower state.")
    
  def handleMessage(self, messageType, message, termNumber):
    message = None
    if messageType == "RequestVote":
      message = protoc.RequestVote()
      message.ParseFromString(message)
      if self.voted:
        self.sendVoteNACK(message.fromNode, termNumber)
      else:
        self.sendVoteACK(message.fromNode, termNumber)
    elif messageType == "AppendEntries":
      # TODO: implement this
      pass

