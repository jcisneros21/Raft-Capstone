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
    print('New Leader state. Term # {}'.format(self.term))

  # Was sendHeartbeat
  def createHeartbeat(self):
    message = protoc.AppendEntries()
    message.term = self.term
    #self.initTimer()
    return protoc.APPENDENTRIES, message

  def handleMessage(self, messageType, message):
    print('Leader got messageType {} from {}'.format(messageType, message.fromAddr))
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
    print('New Candidate state. Term # {}'.format(self.term))
    # Candidate has vote for himself
    self.votes = 1
    self.heardFromLeader = False

  def handleMessage(self, messageType, message):
    print('Candidate got messageType {} from {}'.format(messageType, message.fromAddr))
    if messageType == protoc.REQUESTVOTE:
      if message.term > self.term:
        return self.sendVoteNACK(message.fromAddr, message.fromPort)
    elif messageType == protoc.VOTERESULT:
      print('Message.granted = {}'.format(message.granted))
      if message.granted:
        self.votes += 1
        print('applied vote. new vote count is {}'.format(self.votes))
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
    message.term = self.term
    return protoc.REQUESTVOTE, message

class FollowerState(State):
  def __init__(self, term):
    State.__init__(self, term)
    print('New Follower state. Term # {}'.format(self.term))
    self.voted = False

  def handleMessage(self, messageType, message):
    print('Follower got messageType {} from {}'.format(messageType, message.fromAddr))
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
        self.voted = False
        return self.replyAEACK(message.fromAddr, message.fromPort)
