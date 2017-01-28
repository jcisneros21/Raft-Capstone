#!/usr/bin/env python3
# Run with "py.test StateTesting.py"

import sys
sys.path.append("..")

from State import *
import RaftMessages_pb2 as protoc

def createRepeatedEntries():
  repeated = protoc.LogEntries()
  
  for i in range(0, 10):
    message = repeated.entry.add()
    # message = protoc.AppendEntries()
    message.term = i
    # repeated.entry.append(message)
  
  print(repeated.entry[1].term)


createRepeatedEntries()

