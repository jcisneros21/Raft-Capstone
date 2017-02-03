import threading
import RaftMessages_pb2 as protoc
import random
import json

'''Only write to disk if I send a message
   writeToLog will save a message to a dictionary
   readFromLog will read from dictionary
   We need to have a function where the instance
   of this algorithm will call on startup to
   extract the log that had been saved.
'''

class State():
  def __init__(self, term, logFile, currentLog=None):
    # How do I save a log once I transition?
    # I could make a copy of the log and insert it back
    # once I transition.
    # I could read from file
    if currentLog is None:
      self.log = {}
    else:
      self.log = currentLog
    self.term = term
    # Index of last Commited Entry
    self.commitIndex = 0
    # Current index of last entry
    self.lastApplied = 0
    # The next empty index in the log
    self.nextIndex = 0
    self.logFile = logFile

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
    #message.replyingToEntry = reply       #Need to specify if we are replying to an entry
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

  # Parses a LogEntry Message to write to a log
  def writeToLog(self, message):
    entry = {}
    entry["committed"] = message.committed
    entry["data"] = message.data
    entry["creationTerm"] = message.creationTerm
    entry["logPosition"] = message.logPosition
    self.log[str(entry["logPosition"])] = entry
    self.lastApplied = entry["logPosition"]
    self.nextIndex += 1

    if self.lastApplied == 20:
      self.printLog()
    return True

  # Question, do I return a log message or a dictionary
  # I think a log message so the leader can send entries
  # to other followers in the network
  def readFromLog(self, index):
    entry = self.log[str(index)]
    message = protoc.LogEntry()
    message.committed = False
    message.data = message.info
    message.creationTerm = message.term
    message.logPosition = message.prevLogIndex + 1
    return message

  def removeEntry(self, index):
    entry = self.readToLog(index)
    del self.log[str(index)]
    return entry

  def nextIndex(self):
    pass

  def matchIndex(self):
    pass

  def printLog(self):
    for i in range(0, self.lastApplied):
      entry = self.log[i]
      print()
      print(entry.committed)
      print(entry.data)
      print(entry.creationTerm)
      print(entry.logPosition)
      print()

  def writeLogToFile(self):
    with open(self.logFile, 'w') as fp:
      json.dump(self.log,fp)

  def readLogFromFile(self):
    with open(self.logFile, 'r') as fp:
      self.log = json.load(fp)

  def randText(self):
    word_file = "text.txt"
    words = open(word_file).read().split()
    return random.choice(words)


class LeaderState(State):
  def __init__(self, term, nodeAddrs, logFile, currentLog=None):
    State.__init__(self, term, logFile, currentLog)
    self.totalFollowerIndex = {}
    self.initializeFollowerIndex(nodeAddrs)
    print('New Leader state. Term # {}'.format(self.term))

  def initializeFollowerIndex(self, addressLog):
    for address in addressLog:
      self.totalFollowerIndex[address[0]] = (1,0)

  # This should be called 
  def createAppendEntries(self, entries):
    message = protoc.AppendEntries()
    message.term = self.term
    message.prevLogIndex = entries[0].logPosition - 1
    message.prevLogTerm = entries[0].creationTerm
    message.entries.extend(entries)
    message.leaderCommit = self.commitIndex
    return protoc.APPENDENTRIES, message

  # 1) Send Heartbeats
  # Create AppendEntries where the Server Sends it to all nodes in the network
  # Leader writes it to his own log and sends messages to all followers
  def sendHeartbeat(self):
    messageType, message = protoc.AppendEntries()
    message.term = self.term
    return protoc.APPENDENTRIES, message

  def handleMessage(self, messageType, message):
    print('Leader got messageType {} from {}'.format(messageType, message.fromAddr))
    if messageType is protoc.REQUESTVOTE:
      return self.sendVoteNACK(message.fromAddr, message.fromPort)
    elif messageType is protoc.APPENDENTRIES:
      return self.replyAENACK(message.fromAddr, message.fromPort)
    elif messageType is protoc.APPENDREPLY:
      if message.success:
        index = (self.totalFollowerIndex[message.fromAddr][0] + 1, self.totalFollowerIndex[message.fromAddr][1] + 1)
        self.totalFollowerIndex[message.fromAddr] = index
      else:
        index = (self.totalFollowerIndex[message.fromAddr][0] - 1, self.totalFollowerIndex[message.fromAddr][1])
        return self.createAppendEntries(self.createEntriesList(self.totalFollowerIndex[message.fromAddr][0]))
      if self.commitEntry():
        print("Committed shit.")
      else:
        print("Commit got FUCKED UP")
    else:
      return None, None

  # creates list of log entries from logIndex to end of log
  def createEntriesList(self, logIndex):
    tempList = []
    for i in range(logIndex, len(self.log)):
      tempList.append(self.readFromLog(i))

    return tempList

  def commitEntries(self):
    minIndex = self.totalFollowerIndex[self.totalFollowerIndex.keys()[0]][1]
    for entry in self.totalFollowerIndex.values():
      if(minIndex > entry[1]):
        minIndex = entry[1]

    total = 0
    entryFound = False
    highestIndex = minIndex
    minIndex += 1
    #trying to find HIGHEST index in log that has been replicated on a majority of nodes
    while minIndex < len(self.log):
      for entry in self.totalFollowerIndex.values():
        if(minIndex == entry[1]):
          total += 1
        if total > ((len(self.totalFollowerIndex)+1)//2):
          highestIndex = minIndex

    if self.commitIndex < highestIndex and self.log[str(highestIndex)]["creationTerm"] == self.term:
      for i in range(self.commitIndex, highestIndex + 1):
        self.log[str(i)]["committed"] = True
      self.commitIndex = highestIndex
      return True
    else:
      return False


  # Create a logEntry with the data sent from a client
  # After this is created, the leader should write it to its own
  # log and then send it out to the network.
  def createLogEntry(self, data):
    message = protoc.LogEntry()
    message.committed = False
    message.data = data
    message.creationTerm = self.term
    message.logPosition = self.nextIndex
    return message

class CandidateState(State):
  def __init__(self, term, logFile, currentLog=None):
    State.__init__(self, term, logFile, currentLog)
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

  def requestVote(self):
    message = protoc.RequestVote()
    message.term = self.term
    return protoc.REQUESTVOTE, message

class FollowerState(State):
  def __init__(self, term, logFile, currentLog=None):
    State.__init__(self, term, logFile, currentLog)
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
        # why is this necessary? should this be done some other way?
        self.voted = False
        if str(message.prevLogIndex) not in self.log:
          return self.replyAENACK(message.fromAddr, message.fromPort)
        else:
          #if we have an entry at prevLogIndex, check to see if terms are different
          if self.log[str(message.prevLogIndex)].term != message.prevLogTerm:
            # we need to delete this entry and all that follow it
            for i in range(message.prevLogIndex, self.lastApplied):
              self.removeEntry(i)

        # if we got here, append the new entry
        # Right now we have it as all appendEntries being written to logs
        # self.writeToLog(message)
        if len(message.entries) > 0:
           # Need to update it where it loops through each entry
           self.writeToLog(message)
        if message.leaderCommit > self.commitIndex:
            self.commitIndex = min(message.leaderCommit, message.entries[-1])
            self.commitUpToIndex(self.commitIndex)
        return self.replyAEACK(message.fromAddr, message.fromPort)

    def commitUpToIndex(self, index):
      for i in range(self.commitIndex, index + 1):
        self.log[str(i)]["commited"] = True
