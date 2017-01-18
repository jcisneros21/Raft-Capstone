import threading
import RaftMessages_pb2 as protoc

class State():
  def __init__(self, term):
    self.term = term

  def replyAENACK(self, toAddr, toPort):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = self.term
    message.success = False
    return protoc.APPENDREPLY, message

  def replyAEACK(self, toAddr, toPort):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = self.term
    message.success = True
    return protoc.APPENDREPLY, message

  def sendVoteNACK(self, toAddr, toPort):
    voteack = protoc.VoteResult()
    voteack.toAddr = toAddr
    voteack.toPort = toPort
    voteack.term = self.term
    voteack.granted = False
    return protoc.VOTERESULT, voteack

  def sendVoteACK(self, toAddr, toPort):
    voteack = protoc.VoteResult()
    voteack.toAddr = toAddr
    voteack.toPort = toPort
    voteack.term = self.term
    voteack.granted = True
    return protoc.VOTERESULT, voteack


class LeaderState(State):
  def __init__(self, term):
    State.__init__(self, term)
    print('New Follower state. Term # {}'.format(term))

  def initTimer(self):
    self.timer = threading.Timer(self.heartbeat, self.createHeartbeat)
    self.timer.start()

  # Was sendHeartbeat
  def createHeartbeat(self):
    message = protoc.AppendEntries()
    #self.initTimer()
    return protoc.APPENDENTRIES, message

  def handleMessage(self, messageType, message):
    print('Leader got messageType {}'.format(messageType))
    if messageType is protoc.REQUESTVOTE:
      return self.sendVoteNACK(message.fromAddr, message.fromPort)
    elif messageType is protoc.APPENDENTRIES:
      return self.replyAENACK(message.fromAddr, message.fromPort)
    #elif messageType is protoc.APPENDREPLY
    else:
      return None, None

class CandidateState(State):
  def __init__(self, term):
    State.__init__(self, term)
    print('New Follower state. Term # {}'.format(term))
    # Candidate has vote for himself
    self.votes = 1
    self.heardFromLeader = False

  def handleMessage(self, messageType, message):
    print('Candidate got messageType {}'.format(messageType))
    if messageType == protoc.REQUESTVOTE:
      return self.sendVoteNACK(message.fromAddr, message.fromPort)
    elif messageType == protoc.VOTERESULT:
      if message.granted:
        self.votes += 1
      return None,None
    elif messageType == protoc.APPENDENTRIES:
      if message.term < self.term:
        return self.replyAENACK(message.fromAddr, message.fromPort)
      else:
        # this case is if the term number is = to ours which means we heard
        # from someone who won the election
        return None, None

  def createVote(self):
    message = protoc.RequestVote()
    return protoc.REQUESTVOTE, message

class FollowerState(State):
  def __init__(self, term):
    State.__init__(self, term)
    print('New Follower state. Term # {}'.format(term))
    self.voted = False

  def handleMessage(self, messageType, message):
    print('Follower got messageType {}'.format(messageType))
    # If RequestVote Message is Recieved
    if messageType == protoc.REQUESTVOTE:
      if self.voted:
        return self.sendVoteNACK(message.fromAddr, message.fromPort)
      else:
        self.voted = True
        return self.sendVoteACK(message.fromAddr, message.fromPort)
    # If AppendEntries Message is Recieved
    elif messageType == protoc.APPENDENTRIES:
      if message.term < self.term:
        return self.replyAENACK(message.fromAddr, message.fromPort)
      else:
        return self.replyAEACK(message.fromAddr, message.fromPort)
