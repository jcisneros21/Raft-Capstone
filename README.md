# Raft-Capstone


## Getting Started
  
Below are the instructions for running Raft-Capstone.

### Prerequisites

Setting up a network emulator, for example Mininet, and installing Google Protocol Buffers, and the python version, inside the virtual environment are required before running our implementation of the Raft Algorithm.

Links for instructions to set up both Mininet and Google Protocol Buffers can be found below:

Mininet:  

http://mininet.org/download/


Google's Protocol Buffers README: 
 
https://github.com/google/protobuf

### Running Raft

Once you have the pre-requisites set up, you can then clone the current repository in the virtual environment and begin adding the IP addresses and port numbers of the many virtual hosts you plan to create to the host list "nodeaddrs.txt". 
 
Currently, we only have a static host list where the user must specify the IP address and port number for each host. We plan to create a dynamic host list sometime in the future to allow each host to connect to one another without the user having to specify the network information inside the host list.

Once you have the host list set up, you can then run this exact command on a host to initiate Raft:

```  
python3 test.py
```  


## Authors

* **Fred Trelz**
* **Jessie Cisneros**

## TO-DO

* Fixing current bugs in the system  
  - There seems to be a bug when saving term numbers for each node. Fixing this bug is top priority.

* Testing and Redesigning

* Implementing Dynamic Host List Functionality

* Implementing Fast Raft Functionality

* Implementing ACBBA (Auction Consensus Based Bundle Alogorithm)

* Testing Raft with Different Topologies
