#!/usr/bin/env python3

import sys
import json
sys.path.append("..")

from State import *
import RaftMessages_pb2 as protoc

def json_testing():
  state = State(0, '/home/jcisneros/Documents/GitHub_Repos/Raft-Capstone/Testing/log.txt')
  
  log = {}
  for i in range(0, 10):
    message = protoc.LogEntry()
    message.committed = False
    #message.data = 'phone'
    message.creationTerm = 0
    message.logPosition = i
    log[i] = message

  state.log = log
  state.writeLogToFile()
  state.readLogFromFile()

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

messageSeriz()
