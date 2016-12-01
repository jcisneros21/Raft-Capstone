import server
import RaftMessages_pb2 as protoc

class State():
  def __init__(self, termNumber, server):
    self.termNumber = termNumber  
    self.server = server

  def sendVoteNACK(self, toNode, termNumber):
    voteack = protoc.VoteResult()
    voteack.toNode.add(toNode[0])
    voteack.toNode.add(toNode[1])
    voteack.term = termNumber
    voteack.granted = False
    self.server.talk("VoteResult", voteack)

  def sendVoteACK(self, toNode, termNumber):
    voteack = protoc.VoteResult()
    voteack.toNode.add(toNode[0])
    voteack.toNode.add(toNode[1])
    voteack.term = termNumber
    voteack.granted = True
    self.server.talk("VoteResult", voteack)

class LeaderState(State):
  def __init__(self, termNumber, server):
    State.__init__(self, termNumber, server)
    print("Leader")
    
  #def appendEntries():

  def stop(self):
    print("Stopping leader state.")

class CandidateState(State):
  def __init__(self, termNumber, server):
    State.__init__(self, termNumber, server)
    print("Candidate")
    self.votes = 0
    self.heardFromLeader = False
    self.requestVotes()

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

  def requestVotes(self):
    message = protoc.RequestVote()
    message.term = self.termNumber
    self.server.talk("RequestVote", message)

class FollowerState(State):
  def __init__(self, termNumber, server):
    State.__init__(self, termNumber, server)
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
        self.voted = True
    elif messageType == "AppendEntries":
      # TODO: implement this
      pass

