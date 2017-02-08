import threading
import RaftMessages_pb2 as protoc
import random
import json
import os

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
      sentinel = {}
      sentinel["committed"] = False
      sentinel["data"] = "poop in a hat"
      sentinel["creationTerm"] = 0
      sentinel["logPosition"] = -1
      self.log["-1"] = sentinel    # sentinel value so that we can properly handle first entry
    else:
      self.log = currentLog
    self.term = term
    # Index of last Commited Entry
    self.commitIndex = -1
    # Current index of last entry
    self.lastApplied = -1
    # The next empty index in the log
    self.nextIndex = 0
    self.logFile = logFile

  def replyAENACK(self, toAddr, toPort):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = self.term
    message.success = False
    message.matchIndex = self.lastApplied
    return protoc.APPENDREPLY, message

  def replyAEACK(self, toAddr, toPort):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = self.term
    message.success = True
    message.matchIndex = self.lastApplied
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

    self.writeLogToFile()
    if self.lastApplied == 20:
      self.printLog()
    return True

  # Question, do I return a log message or a dictionary
  # I think a log message so the leader can send entries
  # to other followers in the network
  def readFromLog(self, index):
    entry = self.log[str(index)]
    message = protoc.LogEntry()
    message.committed = entry["committed"]
    message.data = entry["data"]
    message.creationTerm = entry["creationTerm"]
    message.logPosition = entry["logPosition"]
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
    for key in self.log.keys():
        print("committed: {}\ndata: {}\n creationTerm: {}\nlogPosition: {}\n\n".format(self.log[key]['committed'], self.log[key]['data'], self.log[key]['creationTerm'], self.log[key]['logPosition']))

  def writeLogToFile(self):
    if not os.path.isfile(self.logFile):
      # if the log file does not exist yet
      with open(self.logFile, 'w') as fp:
        json.dump(self.log, fp)
    else:
      with open(self.logFile, 'a') as fp:
        json.dump(self.log, fp)

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

  def createAppendEntries(self, toAddr, toPort, entries=[]):
    message = protoc.AppendEntries()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = self.term

    if len(entries) == 0:
      message.prevLogIndex = self.lastApplied
      if self.lastApplied == -1:
        message.prevLogTerm = -1
      else:
        message.prevLogTerm = self.log[str(self.lastApplied)]["creationTerm"]
    else:
      message.prevLogIndex = entries[0].logPosition - 1
      message.prevLogTerm = entries[0].creationTerm
      message.entries.extend(entries)
    message.leaderCommit = self.commitIndex
    return protoc.APPENDENTRIES, message

  def sendHeartbeat(self):
    message = protoc.AppendEntries()
    message.term = self.term
    return protoc.APPENDENTRIES, message

  def handleMessage(self, messageType, message):
    print('Leader got messageType {} from {}'.format(messageType, message.fromAddr))
    if messageType is protoc.REQUESTVOTE:
      # this most likely means we transitioned before we received all vote results
      # just drop the message
      return None,None
    elif messageType is protoc.APPENDENTRIES:
      return self.replyAENACK(message.fromAddr, message.fromPort)
    elif messageType is protoc.APPENDREPLY:
      if message.success:
        print("Got a successful appendentries")
        if (message.matchIndex > self.totalFollowerIndex[message.fromAddr][1]):
          index = (self.totalFollowerIndex[message.fromAddr][0] + 1, self.totalFollowerIndex[message.fromAddr][1] + 1)
          self.totalFollowerIndex[message.fromAddr] = index
      else:
        print("Got a bad appendentries")
        index = (self.totalFollowerIndex[message.fromAddr][0] - 1, self.totalFollowerIndex[message.fromAddr][1])
        self.totalFollowerIndex[message.fromAddr] = index
        return self.createAppendEntries(message.fromAddr, message.fromPort, self.createEntriesList(self.totalFollowerIndex[message.fromAddr][0]))

      if self.lastApplied > -1:
        if self.commitEntries():
          print("committed shit")
        else:
          print("didnt commit shit")

    return None, None

  # creates list of log entries from logIndex to end of log
  def createEntriesList(self, logIndex):
    tempList = []
    for i in range(logIndex, (len(self.log)-1)):
      tempList.append(self.readFromLog(i))

    return tempList

  def commitEntries(self):
    # Step 1: Find smallest match index of all servers
    # here were grabbing the current match index of the first server
    minIndex = self.totalFollowerIndex[list(self.totalFollowerIndex.keys())[0]][1]
    # standard find minimum loop
    for entry in self.totalFollowerIndex.values():
      if(minIndex > entry[1]):
        minIndex = entry[1]

    total = 0
    entryFound = False
    highestIndex = minIndex
    minIndex += 1
    print("\n{}\n".format(self.totalFollowerIndex))
    #trying to find HIGHEST index in log that has been replicated on a majority of nodes
    while minIndex < len(self.log):
      for entry in self.totalFollowerIndex.values():
        if(minIndex == entry[1]):
          total += 1
        if total >= ((len(self.totalFollowerIndex)+1)//2):
          highestIndex = minIndex
      total = 0
      minIndex += 1

    print("highest index: {}\ncommit index: {}".format(highestIndex, self.commitIndex))
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
    self.writeToLog(message)
    return protoc.LOGENTRY, message

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
        print("message.term < self.term")
        return self.replyAENACK(message.fromAddr, message.fromPort)
        # at this point we know something should be in our log so do our normal checks
      if str(message.prevLogIndex) not in self.log.keys():
        print("str(message.prevLogIndex) = {}, log.keys() = {}".format(message.prevLogIndex, self.log.keys()))
        return self.replyAENACK(message.fromAddr, message.fromPort)
      else:
        if message.prevLogIndex != -1: #if we're dealing with the first entry, don't do this
          if self.log[str(message.prevLogIndex)]["creationTerm"] != message.prevLogTerm:
            print("log creation term != message.prevLogTerm")
            return self.replyAENACK(message.fromAddr, message.fromPort)

      if len(message.entries) > 0:
        print("entries = {}".format(message.entries))
        for entry in message.entries:
          if str(message.prevLogIndex) not in self.log.keys():
            if self.log[str(entry.logPosition)]["creationTerm"] != entry.creationTerm:
              deleteFromIndex(entry.logPosition)

        for entry in message.entries:
          self.writeToLog(entry)

      if message.leaderCommit > self.commitIndex:
        self.commitUpToIndex(message.leaderCommit)

      return self.replyAEACK(message.fromAddr, message.fromPort)

  def commitUpToIndex(self, index):
    print("In commitUpToIndex")
    for i in range(self.commitIndex, index + 1):
      print("committing log index {}".format(i))
      self.log[str(i)]["committed"] = True

  def deleteFromIndex(self, index):
    for i in range(index, self.lastApplied + 1):
      self.removeEntry(i)
