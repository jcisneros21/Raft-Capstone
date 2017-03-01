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
    self.log = {}
    readFile = self.readLogFromFile()
    
    higherTerm = self.readTermNumber()
    if higherTerm > self.term:
      self.term = higherTerm

    # If no log has been passed or been read, create a new log
    if not readFile and currentLog is None:
      sentinel = {}
      sentinel["committed"] = True
      sentinel["data"] = ""
      sentinel["creationTerm"] = 0
      sentinel["logPosition"] = -1
      self.log["-1"] = sentinel    
      self.commitIndex = -1
      self.lastApplied = -1
      self.nextIndex = 0
    else:
      # If Log was not read, then use passed in log
      if not readFile:
        self.log = currentLog
      # Index of last Commited Entry
      self.commitIndex = self.findLastCommit(self.log)
      # Index of last added LogEntry
      self.lastApplied = len(self.log) - 2
      # The next empty index in the log
      self.nextIndex = len(self.log) - 1

  # Find the latest index that has been committed
  def findLastCommit(self, log):
    indexCommitted = -1
    for i in range(-1, len(log)-2):
      if log[str(i)]['committed'] is True:
        indexCommitted = i
    return indexCommitted

  # Finds the highest Term Number in the logs
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

  # Retrieve file for saving Term Number
  def getTermFile(self, logfile):
    filename = ''
    if('1' in logfile):
      filename = 'state1.txt'
    elif('2' in logfile):
      filename = 'state2.txt'
    elif('3' in logfile):
      filename = 'state3.txt'
    elif('4' in logfile):
      filename = 'state4.txt'
    elif('5' in logfile):
      filename = 'state5.txt'
    return filename

  # Save Term Number to file
  def saveTermNumber(self):
    filename = self.getTermFile(self.logFile)
    with open(filename, 'w+') as fp:
      fp.write(str(self.term))

  # Retrieve Term Number from file
  def readTermNumber(self):
    termNumber = 0
    filename = self.getTermFile(self.logFile)
    try:
      with open(filename, 'r') as fp:
        for line in fp:
          termNumber = int(line.split()[0])
      return termNumber
    except FileNotFoundError as e:
      return 0

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
    entry = self.readFromLog(index)
    del self.log[str(index)]
    self.lastApplied -= 1
    self.nextIndex -= 1
    return entry
  
  # Prints the Log for Testing Purposes
  def printLog(self):
    for i in range(0,len(self.log)-1):
      entry = self.log[str(i)]
      print("committed: {}".format(entry['committed']))
      print("data: {}".format(entry['data']))
      print("creationTerm: {}".format(entry['creationTerm']))
      print("logPosition: {}\n".format(entry['logPosition']))

  # Prints certain logEntry in the log
  def printLogEntry(self, index):
    entry = self.log[str(index)]
    print("committed: {}".format(entry['committed']))
    print("data: {}".format(entry['data']))
    print("creationTerm: {}".format(entry['creationTerm']))
    print("logPosition: {}\n".format(entry['logPosition']))  

  # Writes the Log to the logFile stated
  def writeLogToFile(self):
    with open(self.logFile, 'w+') as fp:
      json.dump(self.log, fp, sort_keys=True, indent=2, separators=(',',': '))

  # Extracts a Saved Log from logFile 
  def readLogFromFile(self):
    if not os.path.isfile(self.logFile):
      f = open(self.logFile, 'w+')
      f.close()
      
    try:
      with open(self.logFile, 'r') as fp:
        self.log = json.load(fp)
    except ValueError:
        return False

    if(len(self.log) > 0):
      return True
    else:
      return False

''' 
    The Leader State will initiate communication with all other
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
    self.totalFollowerIndex = {}
    self.initializeFollowerIndex(nodeAddrs)
    print('New Leader state. Term # {}\n'.format(self.term))
    self.saveTermNumber()

  # Initializes all Follower's commit index and match index
  def initializeFollowerIndex(self, addressLog):
    for address in addressLog:
      self.totalFollowerIndex[address[0]] = (-1,-1)

  # Creates the AppendEntries Messages for the server
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
   
    # Leader should reject any messages from Candidates
    if messageType is protoc.REQUESTVOTE:
      return None,None
    # Leader should reject any messages from other Leaders
    elif messageType is protoc.APPENDENTRIES:
      return self.replyAENACK(message.fromAddr, message.fromPort)
    # Retrieve a Message from a Follower
    elif messageType is protoc.APPENDREPLY:
      if message.success:
        # If the Follower has appended a LogEntry, update that Follower's commit and match index
        if (message.matchIndex > self.totalFollowerIndex[message.fromAddr][1]):
          index = (message.matchIndex - 1, message.matchIndex)
          self.totalFollowerIndex[message.fromAddr] = index
      else:
        # Preform Node Recovery
        if self.totalFollowerIndex[message.fromAddr][0] > -1:
          index = (self.totalFollowerIndex[message.fromAddr][0] - 1, message.matchIndex)
          self.totalFollowerIndex[message.fromAddr] = index
        return self.createAppendEntries(message.fromAddr, message.fromPort, self.createEntriesList(self.totalFollowerIndex[message.fromAddr][0]))

      # Test to commit LogEntries
      if self.lastApplied > -1:
        if self.commitEntries():
            pass
            #print("Committed Entries")
        else:
            pass
            #print("Couldn't Commit Entries")

    return None, None

  # Create a list of entries to send the Follower starting from logIndex
  def createEntriesList(self, logIndex):
    tempList = []
    for i in range(logIndex, (len(self.log)-1)):
      # This is a bug in general
      if i > -1:
        tempList.append(self.readFromLog(i))
    return tempList


  # Commit Logic for the LogEntry Messages 
  def commitEntries(self):
 
    # TO-DO: will always refer to -1 as the lowest, may need to optimize this
    minIndex = self.totalFollowerIndex[list(self.totalFollowerIndex.keys())[0]][1]

    # Find the minimum matchIndex value
    for entry in self.totalFollowerIndex.values():
      if(minIndex > entry[1]):
        minIndex = entry[1]

    total = 0
    entryFound = False
    highestIndex = minIndex
    minIndex += 1

    # Find the HIGHEST INDEX in all logs that has been replicated on a majority of nodes
    while minIndex < len(self.log):
      for entry in self.totalFollowerIndex.values():
        if(minIndex == entry[1]):
          total += 1
        if total >= ((len(self.totalFollowerIndex)+1)//2):
          highestIndex = minIndex
      total = 0
      minIndex += 1

    
    # If there is a higher value then the commitIndex and that entry is in the current term
    if self.commitIndex < highestIndex and self.log[str(highestIndex)]["creationTerm"] == self.term:
      for i in range(self.commitIndex + 1, highestIndex + 1):
        self.log[str(i)]["committed"] = True
      self.commitIndex = highestIndex
      self.writeLogToFile()
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
    self.printLogEntry(self.lastApplied)
    return protoc.LOGENTRY, message



''' 
    The Candidate State handles the voting process to transition
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
    self.votes = 1
    self.heardFromLeader = False
    self.saveTermNumber()

  def handleMessage(self, messageType, message):

    # Reply False to other VoteRequest Messages since the Candidate has already voted
    if messageType == protoc.REQUESTVOTE:
      return self.sendVoteNACK(message.fromAddr, message.fromPort)
    # Stores granted votes
    elif messageType == protoc.VOTERESULT:
      if message.granted:
        print('Candidate got messageType {} from {}.'.format(messageType, message.fromAddr))
        self.votes += 1
        print('Total votes: {}.\n'.format(self.votes))
      return None,None
    # Reply False to any AppendEntry Messages
    elif messageType == protoc.APPENDENTRIES:
      if message.term < self.term:
        return self.replyAENACK(message.fromAddr, message.fromPort)
      else:
        return None, None

  # Creates RequestVote Messages
  def requestVote(self):
    message = protoc.RequestVote()
    message.term = self.term
    return protoc.REQUESTVOTE, message


class FollowerState(State):
  def __init__(self, term, logFile, currentLog=None):
    State.__init__(self, term, logFile, currentLog)
    print('New Follower state. Term # {}\n'.format(self.term))
    self.voted = False
    self.saveTermNumber()

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
        return self.replyAENACK(message.fromAddr, message.fromPort)
      # Missing log entries
      if str(message.prevLogIndex) not in self.log.keys():
        return self.replyAENACK(message.fromAddr, message.fromPort)
      else:
        if message.prevLogIndex != -1: 
          # If there are entries that don't match the leader's log
          if self.log[str(message.prevLogIndex)]["creationTerm"] != message.prevLogTerm:
            return self.replyAENACK(message.fromAddr, message.fromPort)

      # Delete entries if they don't match the leader's log
      if len(message.entries) > 0:
        for entry in message.entries:
          if str(entry.logPosition) in self.log.keys():
            if self.log[str(entry.logPosition)]["creationTerm"] != entry.creationTerm:
              print("\nDeleting logEntry.\n")
              self.printLogEntry(entry.logPosition)
              self.deleteFromIndex(entry.logPosition)

        # Add entries to the Follower's Log
        for entry in message.entries:
          if(entry.logPosition > self.lastApplied):
            print("\nAdding LogEntry.\n")
            self.writeToLog(entry)
            self.printLogEntry(self.lastApplied)

      # Commit entries in Follower's Log
      if message.leaderCommit > self.commitIndex:
        self.commitUpToIndex(message.leaderCommit)
        self.writeLogToFile()

      return self.replyAEACK(message.fromAddr, message.fromPort)

  # Commit entries from index
  def commitUpToIndex(self, index):
    for i in range(self.commitIndex, index + 1):
      self.log[str(i)]["committed"] = True

  # Delete Log Entry of index
  def deleteFromIndex(self, index):
    self.removeEntry(index)
