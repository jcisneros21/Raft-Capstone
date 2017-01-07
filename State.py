import threading
import RaftMessages_pb2 as protoc

class State():
  def __init__(self):
    self.term = 0

  def replyAENACK(self, toAddr, toPort, term):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = term
    message.success = False
    return protoc.APPENDREPLY, message

  def replyAEACK(self, toAddr, toPort, term):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = term
    message.success = True
    return protoc.APPENDREPLY, message

  def sendVoteNACK(self, toAddr, toPort, term):
    voteack = protoc.VoteResult()
    voteack.toAddr = toAddr
    voteack.toPort = toPort
    voteack.term = term
    voteack.granted = False
    return protoc.VOTERESULT, voteack

  def sendVoteACK(self, toAddr, toPort, term):
    voteack = protoc.VoteResult()
    voteack.toAddr = toAddr
    voteack.toPort = toPort
    voteack.term = term
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
    #self.initTimer()
    return protoc.APPENDENTRIES, message

  # TO-DO
  def handleMessage(self, messageType, message, term):
    return None,None


class CandidateState(State):
  def __init__(self):
    State.__init__(self)
    # Candidate has vote for himself
    self.votes = 1
    self.heardFromLeader = False
    #self.requestVotes()

  def handleMessage(self, messageType, message, term):
    if messageType == protoc.REQUESTVOTE:
      return self.sendVoteNACK(message.fromAddr, message.fromPort, term)
    elif messageType == protoc.VOTERESULT:
      if message.granted:
        self.votes += 1
      return None,None
    elif messageType == protoc.APPENDENTRIES:
      if message.term < term:
        return self.replyAENACK(message.fromAddr, message.fromPort, term)

  def requestVotes(self):
    message = protoc.RequestVote()
    return protoc.REQUESTVOTE, message


class FollowerState(State):
  def __init__(self):
    State.__init__(self)
    self.voted = False

  def handleMessage(self, messageType, message, term):
    # If RequestVote Message is Recieved
    if messageType == protoc.REQUESTVOTE:
      if self.voted:
        return self.sendVoteNACK(message.fromAddr, message.fromPort, term)
      else:
        self.voted = True
        return self.sendVoteACK(message.fromAddr, message.fromPort, term)
    # If AppendEntries Message is Recieved
    elif messageType == protoc.APPENDENTRIES:
      if message.term < term:
        return self.replyAENACK(message.fromAddr, message.fromPort, term)
      else:
        return self.replyAEACK(message.fromAddr, message.fromPort, term)
