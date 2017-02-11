import threading
import RaftMessages_pb2 as protoc
import random
import json
import os

''' The State Class is an Abstract Class that holds certain
    functionality that will be passed on to its children.
'''

class State():
  def __init__(self, term, logFile, currentLog=None):
    self.term = term
    self.logFile = logFile
    self.StateFlag = False
    self.log = {}
    readFile = self.readLogFromFile()
    # If the log is not written too
    if not readFile and currentLog is None:
      print("Creating New Log")
      #self.log = {}
      sentinel = {}
      sentinel["committed"] = False
      sentinel["data"] = "poop in a hat"
      sentinel["creationTerm"] = 0
      sentinel["logPosition"] = -1
      self.log["-1"] = sentinel    # sentinel value so that we can properly handle first entry
      self.commitIndex = -1
      self.lastApplied = -1
      self.nextIndex = 0
    else:
      if not readFile:
        self.log = currentLog
      # Index of last Commited Entry
      self.commitIndex = self.findLastCommit(self.log)
      higherTerm = self.findHighestTerm(self.log)
      if higherTerm > self.term:
        self.term = higherTerm 
      # Current index of last entry
      self.lastApplied = len(self.log) - 2
      # The next empty index in the log
      self.nextIndex = len(self.log) - 1

  def findLastCommit(self, log):
    indexCommitted = -1
    for i in range(-1, len(log)-2):
      if log[str(i)]['committed'] is True:
        indexCommitted = i
    return indexCommitted

  # Is it a problem if the algorithm is not erasing any entries if the current term is less?
  def findHighestTerm(self, log):
    lastIndex = len(log) - 2
    return log[str(lastIndex)]['creationTerm']       
  
  # Reply False to AppendEntry Message
  def replyAENACK(self, toAddr, toPort):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = self.term
    message.success = False
    message.matchIndex = self.lastApplied
    return protoc.APPENDREPLY, message
  
  # Reply True to AppendEntry Message
  def replyAEACK(self, toAddr, toPort):
    message = protoc.AppendReply()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = self.term
    message.success = True
    message.matchIndex = self.lastApplied
    return protoc.APPENDREPLY, message

  # Reply False to VoteRequest Message
  def sendVoteNACK(self, toAddr, toPort):
    voteack = protoc.VoteResult()
    voteack.toAddr = toAddr
    voteack.toPort = toPort
    voteack.term = self.term
    voteack.granted = False
    return protoc.VOTERESULT, voteack

  # Reply True to VoteRequest Message
  def sendVoteACK(self, toAddr, toPort):
    voteack = protoc.VoteResult()
    voteack.toAddr = toAddr
    voteack.toPort = toPort
    voteack.term = self.term
    voteack.granted = True
    return protoc.VOTERESULT, voteack

  # Stores a Dictionary of a LogEntry Message into a Log
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
    return True

  # Return an indexed LogEntry Message
  def readFromLog(self, index):
    entry = self.log[str(index)]
    message = protoc.LogEntry()
    message.committed = entry["committed"]
    message.data = entry["data"]
    message.creationTerm = entry["creationTerm"]
    message.logPosition = entry["logPosition"]
    return message

  # Remove a LogEntry from the Log
  def removeEntry(self, index):
    entry = self.readToLog(index)
    del self.log[str(index)]
    return entry
  
  # TO-DO
  def nextIndex(self):
    pass

  def matchIndex(self):
    pass

  
  # Prints the Log for Testing Purposes
  def printLog(self):
    for i in range(-1,self.lastApplied+1):
      entry = self.log[str(i)]
      print("committed: {}".format(entry['committed']))
      print("data: {}".format(entry['data']))
      print("creationTerm: {}".format(entry['creationTerm']))
      print("logPosition: {}\n".format(entry['logPosition']))

  # Writes the Log to the logFile stated
  def writeLogToFile(self):
    if not os.path.isfile(self.logFile):
      # if the log file does not exist yet
      with open(self.logFile, 'w') as fp:
        json.dump(self.log, fp)
    else:
      with open(self.logFile, 'w') as fp:
        json.dump(self.log, fp)

  # Extracts a Saved Log from logFile 
  def readLogFromFile(self):
    try:
      with open(self.logFile, 'r') as fp:
        print("It read the file")
        self.log = json.load(fp)
    except ValueError:
        print("There was an error")
        return False

    print("This is the length of the log: {}".format(len(self.log)))
    if(len(self.log) > 0):
      return True
    else:
      return False

''' The Leader State will initiate communication with all other
    Follower States on the network. This communication involves
    sending Heartbeat Messages to provide confirmation that there
    is a leader present and sending AppendEntry Messages to append
    and commit a LogEntry to logs. The Leader State is the only
    allowed State to create LogEntry Messages to store and send
    on the network.
'''

class LeaderState(State):
  def __init__(self, term, nodeAddrs, logFile, currentLog):
    State.__init__(self, term, logFile, currentLog)
    print()
    print(currentLog)
    print()
    self.totalFollowerIndex = {}
    self.initializeFollowerIndex(nodeAddrs)
    print('New Leader state. Term # {}\n'.format(self.term))

  # Initializes all Follower's commit index and match index
  def initializeFollowerIndex(self, addressLog):
    for address in addressLog:
      self.totalFollowerIndex[address[0]] = (1,0)

  # Creates the AppendEntries Messages for the server
  # Heartbeats are AppendEntry Messages without LogEntry Messages
  def createAppendEntries(self, toAddr, toPort, entries=[]):
    message = protoc.AppendEntries()
    message.toAddr = toAddr
    message.toPort = toPort
    message.term = self.term
    
    # Send a Heartbeat Message
    if len(entries) == 0:
      message.prevLogIndex = self.lastApplied
      if self.lastApplied == -1:
        message.prevLogTerm = -1
      else:
        message.prevLogTerm = self.log[str(self.lastApplied)]["creationTerm"]
    # Send a AppendEntry Message
    else:
      message.prevLogIndex = entries[0].logPosition - 1
      message.prevLogTerm = entries[0].creationTerm
      message.entries.extend(entries)
    message.leaderCommit = self.commitIndex
    return protoc.APPENDENTRIES, message

  # Handles incoming Messages from other states on the network
  def handleMessage(self, messageType, message):
    if self.StateFlag:
      print('Leader got messageType {} from {}\n'.format(messageType, message.fromAddr))
   
    # Leader should reject any messages from Candidates
    if messageType is protoc.REQUESTVOTE:
      return None,None
    # Leader should reject any messages from other Leaders
    elif messageType is protoc.APPENDENTRIES:
      return self.replyAENACK(message.fromAddr, message.fromPort)
    # Retrieve a Message from a Follower
    elif messageType is protoc.APPENDREPLY:
      if message.success:
        if self.StateFlag:
          print("Got a successful appendentries\n")
        # If the Follower has appended a LogEntry, update that Follower's commit and match index
        if (message.matchIndex > self.totalFollowerIndex[message.fromAddr][1]):
          index = (self.totalFollowerIndex[message.fromAddr][0] + 1, message.matchIndex)
          self.totalFollowerIndex[message.fromAddr] = index
      else:
        if self.StateFlag:
          print("Got a bad appendentries\n")
        # Send the Follower missing LogEntries
        index = (self.totalFollowerIndex[message.fromAddr][0] - 1, message.matchIndex)
        self.totalFollowerIndex[message.fromAddr] = index
        return self.createAppendEntries(message.fromAddr, message.fromPort, self.createEntriesList(self.totalFollowerIndex[message.fromAddr][0]))

      # Test to commit LogEntries
      if self.lastApplied > -1:
        if self.commitEntries():
          if self.StateFlag:
            print("committed shit")
        else:
          if self.StateFlag:
            print("didnt commit shit")

    return None, None

  # Create a list of entries beginning with the given index to the current index of the log 
  def createEntriesList(self, logIndex):
    tempList = []
    for i in range(logIndex, (len(self.log)-1)):
      tempList.append(self.readFromLog(i))
    return tempList

  # Commit Logic for the LogEntry Messages 
  def commitEntries(self):
 
    minIndex = self.totalFollowerIndex[list(self.totalFollowerIndex.keys())[0]][1]
    # standard find minimum loop
    for entry in self.totalFollowerIndex.values():
      if(minIndex > entry[1]):
        minIndex = entry[1]

    total = 0
    entryFound = False
    highestIndex = minIndex
    minIndex += 1
    if self.StateFlag:
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

    if self.StateFlag:
      print("highest index: {}\ncommit index: {}\n".format(highestIndex, self.commitIndex))
    if self.commitIndex < highestIndex and self.log[str(highestIndex)]["creationTerm"] == self.term:
      print("Went into the last step of commit logic")
      for i in range(self.commitIndex, highestIndex + 1):
        self.log[str(i)]["committed"] = True
      self.commitIndex = highestIndex
      return True
    else:
      return False

  # Creates a logEntry Message with the data the user enters
  def createLogEntry(self, data):
    message = protoc.LogEntry()
    message.committed = False
    message.data = data
    message.creationTerm = self.term
    message.logPosition = self.nextIndex
    self.writeToLog(message)
    return protoc.LOGENTRY, message

''' The Candidate State handles the voting process to transition
    into a Leader. Once a Candidate has arised, it will create 
    RequestVote Messages to send to all Followers on the network. 
    It should then recieve VoteReply Messages to store the number 
    of successful votes it recieves. Once it reacieves a majority 
    of votes from the network, it will then transition to Leader.
'''

class CandidateState(State):
  def __init__(self, term, logFile, currentLog=None):
    State.__init__(self, term, logFile, currentLog)
    print('New Candidate state. Term # {}\n'.format(self.term))
    # Candidate will always vote for himself
    self.votes = 1
    self.heardFromLeader = False

  def handleMessage(self, messageType, message):
    if self.StateFlag:
      print('Candidate got messageType {} from {}\n'.format(messageType, message.fromAddr))
    # Reply False to other VoteRequest Messages since the Candidate has already voted
    if messageType == protoc.REQUESTVOTE:
      return self.sendVoteNACK(message.fromAddr, message.fromPort)
    # Stores the VoteResult Messages
    elif messageType == protoc.VOTERESULT:
      if self.StateFlag:
        print('Message.granted = {}\n'.format(message.granted))
      if message.granted:
        self.votes += 1
        print('applied vote. new vote count is {}\n'.format(self.votes))
      return None,None
    # Reply False to any AppendEntry Messages
    elif messageType == protoc.APPENDENTRIES:
      if message.term < self.term:
        return self.replyAENACK(message.fromAddr, message.fromPort)
      else:
        # this case is if the term number is = to ours which means we heard
        # from someone who won the election
        return None, None

  # Creates RequestVote Messages
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
        if self.StateFlag:
          print("message.term < self.term")
        return self.replyAENACK(message.fromAddr, message.fromPort)
        # at this point we know something should be in our log so do our normal checks
      if str(message.prevLogIndex) not in self.log.keys():
        if self.StateFlag:
          print("str(message.prevLogIndex) = {}, log.keys() = {}".format(message.prevLogIndex, self.log.keys()))
        return self.replyAENACK(message.fromAddr, message.fromPort)
      else:
        if message.prevLogIndex != -1: #if we're dealing with the first entry, don't do this
          if self.log[str(message.prevLogIndex)]["creationTerm"] != message.prevLogTerm:
            if self.StateFlag:
              print("log creation term != message.prevLogTerm")
            return self.replyAENACK(message.fromAddr, message.fromPort)

      if len(message.entries) > 0:
        if self.StateFlag:
          print("entries = {}".format(message.entries))
        for entry in message.entries:
          if str(message.prevLogIndex) not in self.log.keys():
            if self.log[str(entry.logPosition)]["creationTerm"] != entry.creationTerm:
              print("\nDeleting Entry\n")
              deleteFromIndex(entry.logPosition)

        for entry in message.entries:
          self.writeToLog(entry)

      if message.leaderCommit > self.commitIndex:
        self.commitUpToIndex(message.leaderCommit)

      return self.replyAEACK(message.fromAddr, message.fromPort)

  def commitUpToIndex(self, index):
    if self.StateFlag:
      print("In commitUpToIndex")
    for i in range(self.commitIndex, index + 1):
      if self.StateFlag:
        print("committing log index {}".format(i))
      self.log[str(i)]["committed"] = True

  def deleteFromIndex(self, index):
    for i in range(index, self.lastApplied + 1):
      self.removeEntry(i)
