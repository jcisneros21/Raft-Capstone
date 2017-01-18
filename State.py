import threading
import RaftMessages_pb2 as protoc

class State():
  def __init__(self,term):
    self.term = term

  def createAENACK(self, toAddr, toPort, term):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = term
    message.success = False
    return protoc.APPENDREPLY, message

  def createAEACK(self, toAddr, toPort, term):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = term
    message.success = True
    return protoc.APPENDREPLY, message

  def createVoteNACK(self, toAddr, toPort, term):
    voteack = protoc.VoteResult()
    voteack.toAddr = toAddr
    voteack.toPort = toPort
    voteack.term = term
    voteack.granted = False
    return protoc.VOTERESULT, voteack

  def createVoteNACK(self, toAddr, toPort, term):
    voteack = protoc.VoteResult()
    voteack.toAddr = toAddr
    voteack.toPort = toPort
    voteack.term = term
    voteack.granted = True
    return protoc.VOTERESULT, voteack


class LeaderState(State):
  def __init__(self):
    State.__init__(self,term)
    self.term = term
    # Send Heartbeats once transitioned to inform a leader is present
    self.createHeartbeat()
    # Time interval to send messages in seconds
    self.heartbeat = 4
    self.timer = None

  def initTimer(self):
    self.timer = threading.Timer(self.heartbeat, self.createHeartbeat)
    self.timer.start()

  # Was sendHeartbeat
  def createHeartbeat(self):
    message = protoc.AppendEntries()
    #self.initTimer()
    return protoc.APPENDENTRIES, message

  # TO-DO
  def handleMessage(self, messageType, message, term):
    return None,None


class CandidateState(State):
  def __init__(self):
    State.__init__(self,term)
    self.term = term
    # Candidate has vote for himself
    self.votes = 1
    self.heardFromLeader = False
    #self.createVote()

  def handleMessage(self, messageType, message, term):
    if messageType == protoc.REQUESTVOTE:
      return self.createVoteNACK(message.fromAddr, message.fromPort, term)
    elif messageType == protoc.VOTERESULT:
      if message.granted:
        self.votes += 1
      return None,None
    elif messageType == protoc.APPENDENTRIES:
      if message.term < term:
        return self.createAENACK(message.fromAddr, message.fromPort, term)

  def createVote(self):
    message = protoc.RequestVote()
    return protoc.REQUESTVOTE, message


class FollowerState(State):
  def __init__(self):
    State.__init__(self,term)
    self.term = term
    self.voted = False

  def handleMessage(self, messageType, message, term):
    # If RequestVote Message is Recieved
    if messageType == protoc.REQUESTVOTE:
      if self.voted:
        return self.createVoteNACK(message.fromAddr, message.fromPort, term)
      else:
        self.voted = True
        return self.createVoteNACK(message.fromAddr, message.fromPort, term)
    # If AppendEntries Message is Recieved
    elif messageType == protoc.APPENDENTRIES:
      if message.term < term:
        return self.createAENACK(message.fromAddr, message.fromPort, term)
      else:
        return self.createAEACK(message.fromAddr, message.fromPort, term)
