import threading
import RaftMessages_pb2 as protoc

class State():
  def __init__(self):
    self.termNumber = 0 

  def replyAENACK(self, toAddr, toPort, termNumber):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = termNumber
    message.success = False
    return protoc.APPENDREPLY, message

  def replyAEACK(self, toAddr, toPort, termNumber):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = termNumber
    message.success = True
    return protoc.APPENDREPLY, message

  def sendVoteNACK(self, toAddr, toPort, termNumber):
    voteack = protoc.VoteResult()
    voteack.toAddr = toAddr
    voteack.toPort = toPort
    voteack.term = termNumber
    voteack.granted = False
    return protoc.VOTERESULT, voteack

  def sendVoteACK(self, toAddr, toPort, termNumber):
    voteack = protoc.VoteResult()
    voteack.toAddr = toAddr
    voteack.toPort = toPort
    voteack.term = termNumber
    voteack.granted = True
    return protoc.VOTERESULT, voteack


class LeaderState(State):
  def __init__(self):
    State.__init__(self)
    # Send Heartbeats once transitioned to inform a leader is present
    self.sendHeartbeat()
    # Time interval to send messages in seconds
    self.heartbeat = 4
    self.timer = None
  
  def initTimer(self):
    self.timer = threading.Timer(self.heartbeat, self.sendHeartbeat)
    self.timer.start()

  def sendHeartbeat(self):
    message = protoc.AppendEntries()
    self.initTimer()
    return protoc.APPENDENTRIES, message

  # TO-DO
  def handleMessage(self, messageType, message, termNumber):
    pass


class CandidateState(State):
  def __init__(self):
    State.__init__(self)
    # Candidate has vote for himself
    self.votes = 1  
    self.heardFromLeader = False
    self.requestVotes()

  def handleMessage(self, messageType, message, termNumber):
    if messageType == protoc.REQUESTVOTE:
      return self.sendVoteNACK(message.fromAddr, message.fromPort, termNumber)
    elif messageType == protoc.VOTERESULT:
      if message.granted:
        self.votes += 1
    elif messageType == protoc.APPENDENTRIES:
      if message.term < termNumber:
        return self.replyAENACK(message.fromAddr, message.fromPort, termNumber)
      else:
        # When will this ever happen?
        self.heardFromLeader = True

  def requestVotes(self):
    message = protoc.RequestVote()
    return protoc.REQUESTVOTE, message


class FollowerState(State):
  def __init__(self):
    State.__init__(self)
    self.voted = False
  
  def handleMessage(self, messageType, message, termNumber):
    # If RequestVote Message is Recieved
    if messageType == protoc.REQUESTVOTE:
      if self.voted:
        return self.sendVoteNACK(message.fromAddr, message.fromPort, termNumber)
      else:
        self.voted = True
        return self.sendVoteACK(message.fromAddr, message.fromPort, termNumber)
    # If AppendEntries Message is Recieved
    elif messageType == protoc.APPENDENTRIES:
      if message.term < termNumber:
        return self.replyAENACK(message.fromAddr, message.fromPort, termNumber)
      else:
        return self.replyAEACK(message.fromAddr, message.fromPort, termNumber)
