#!/usr/bin/env python3

import sys
import json
sys.path.append("..")

from State import *
import RaftMessages_pb2 as protoc

# What happens if I parse from an AppendEntry
# what happens if I parse from an LogEntry

def json_testing():
  state = State(0, '/home/jcisneros/Documents/GitHub_Repos/Raft-Capstone/Testing/log.txt')
  
  log = {}
  for i in range(0, 10):
    entry = {}
    entry["committed"] = False
    entry["data"] = 'phone'
    entry["creationTerm"] = 0
    entry["logPosition"] = i 
    log[i] = entry

  state.log = log
  state.writeLogToFile()
 
  state = State(0, 'log.txt')
  print("Going to read from logs")
  state.readLogFromFile()
  print(state.log)
  print(state.log[0])

def messageSeriz():
  message = protoc.LogEntry()
  message.committed = False
  message.creationTerm = 0
  message.logPosition = 0
  
  with open("log.txt","w") as fp:
    json.dump(message.__dict__, fp)

def dictionary():
  message = {0:{"success":True}}
  
  with open("log.txt","w") as fp:
    json.dump(message, fp)

json_testing()
