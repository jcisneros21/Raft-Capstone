import server
import RaftMessages_pb2 as protoc

class State():
  def __init__(self, termNumber, server):
    self.termNumber = termNumber  
    self.server = server

  def sendVoteNACK(self, toAddr, toPort, termNumber):
    voteack = protoc.VoteResult()
    voteack.toAddr = toAddr
    voteack.toPort = toPort
    voteack.term = termNumber
    voteack.granted = False
    self.server.talk(protoc.VOTERESULT, voteack)

  def sendVoteACK(self, toAddr, toPort, termNumber):
    voteack = protoc.VoteResult()
    voteack.toAddr = toAddr
    voteack.toPort = toPort
    voteack.term = termNumber
    voteack.granted = True
    self.server.talk(protoc.VOTERESULT, voteack)

  def replyAENACK(self, toAddr, toPort, termNumber):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = termNumber
    message.success = False
    self.server.talk(protoc.APPENDREPLY, message)

  def replyAEACK(self, toAddr, toPort, termNumber):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = termNumber
    message.success = True
    self.server.talk(protoc.APPENDREPLY, message)   

class LeaderState(State):
  def __init__(self, termNumber, server):
    State.__init__(self, termNumber, server)
    self.sendHeartbeat()
    self.heartbeat = 2  # interval between heartbeat messages (this must be less than election timout lower bound)
    
  def initTimer(self):
    self.timer = threading.Timer(self.heartbeat, self.sendHeartbeat)
    self.timer.start()

  def sendHeartbeat(self):
    message = protoc.AppendEntries()
    self.server.talk(protoc.APPENDENTRIES, message)

  def handleMessage(self, messageType, message, termNumber):
    pass

  def stop(self):
    pass

class CandidateState(State):
  def __init__(self, termNumber, server):
    State.__init__(self, termNumber, server)
    self.votes = 1   # init this to 1 because each candidate votes for themselves
    self.heardFromLeader = False
    self.requestVotes()

  def stop(self):
    pass

  def handleMessage(self, messageType, message, termNumber):
    if messageType == protoc.REQUESTVOTE:
      self.sendVoteNACK(message.fromAddr, message.fromPort, termNumber)
    elif messageType == protoc.APPENDENTRIES:
      if message.term < termNumber:
        self.replyAENACK(message.fromAddr, message.fromPort, termNumber)
      else:
        self.heardFromLeader = True
    elif messageType == protoc.VOTERESULT:
      if message.granted:
        self.votes += 1
      print("We have {} votes".format(self.votes))
      print()

  def requestVotes(self):
    message = protoc.RequestVote()
    self.server.talk(protoc.REQUESTVOTE, message)

class FollowerState(State):
  def __init__(self, termNumber, server):
    State.__init__(self, termNumber, server)
    self.voted = False

  def stop(self):
    pass

  
  def handleMessage(self, messageType, message, termNumber):
    if messageType == protoc.REQUESTVOTE:
      if self.voted:
        self.sendVoteNACK(message.fromAddr, message.fromPort, termNumber)
      else:
        self.sendVoteACK(message.fromAddr, message.fromPort, termNumber)
        self.voted = True
    elif messageType == protoc.APPENDENTRIES:
      if message.term < termNumber:
        self.replyAENACK(message.fromAddr, message.fromPort, termNumber)
      else:
        self.replyAEACK(message.fromAddr, message.fromPort, termNumber)

