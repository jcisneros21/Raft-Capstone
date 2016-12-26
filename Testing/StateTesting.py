#!/usr/bin/env python3
# Run with "py.test StateTesting.py"

import sys
sys.path.append("..")

from State import *
import RaftMessages_pb2 as protoc

def assert_argument_testing(message, addr, port, term):
  assert message[1].toAddr == addr
  assert message[1].toPort == port
  assert message[1].term == term

def testing_messages():
  state = State()
  message = None
  addr = "10.0.0.1"
  port = 9000
  term = 1
 
  # Testing AppendEntries NACK message
  message = state.replyAENACK(addr, port, term)
  assert message[0] == protoc.APPENDREPLY
  assert_argument_testing(message, addr, port, term)
  assert message[1].success == False

  # Testing AppendEntries ACK message
  message = state.replyAEACK(addr, port, term)
  assert message[0] == protoc.APPENDREPLY
  assert_argument_testing(message, addr, port, term)
  assert message[1].success == True

  # Testing RequestVote NACK message
  message = state.sendVoteNACK(addr, port, term)
  assert message[0] == protoc.VOTERESULT
  assert_argument_testing(message, addr, port, term)
  assert message[1].granted == False

  # Testing RequestVote ACK message
  message = state.sendVoteACK(addr, port, term)
  assert message[0] == protoc.VOTERESULT
  assert_argument_testing(message, addr, port, term)
  assert message[1].granted == True
