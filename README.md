# Raft-Capstone

## Getting Started

### Prerequisites

Setting up a network emulator, for example Mininet, and installing Google Protocol Buffers, and the python version, inside the virtual environment are required before running our implementation of the Raft Algorithm.

Links of instructions to set up both Mininet and Google Protocol Buffers can be found below:

Mininet:
http://mininet.org/download/

Google's Protocol Buffers README:
https://github.com/google/protobuf

### Running Raft

Once you have the pre-requisites set up, you can then clone the current repository and begin adding the ip addresses and port numbers of the many virtual hosts you plan to create to the host list. Currently, we have a static host list were the user must specify the ip address and port number for each host. We plan to create a dynamic host list sometime in the future to allow each host to connect to one another without the user having to type in the network information for each host.

Once you have the host list set up, you can then run this exact command on a host to initiate Raft:

'''
python3 test.py
'''

## Authors

* **Fred Trelz**
* **Jessie Cisneros**

## TO-DO
