# Raft-Capstone
This is the alpha version of our CSCI 4962 capstone project.  We are seniors at Saint Louis University developing our own version of the Raft consensus protocol. Below is an explanation of what our project is and how it works.

Raft is an asynchronous, fault-tolerant, distributed consensus algorithm created by Diego Ongaro and John Ousterhout of Stanford University.  Raft was intended to be an alternative to Leslie Lamport's Paxos algorithm.  It is designed to be simpler, more understandable, and easier to implement than Paxos.  To learn more about the details of Raft and to better understand our implementation please refer to Ongaro and Ousterhout's paper "In Search of an Understandable Consensus Algorithm" (https://raft.github.io/raft.pdf).

Our goal for this project goes beyond simply creating another implementation of Raft.  We wanted to create a more portable, independent, and dynamic implementation that could be used in a variety of different hardware, software, and network circumstances for various experimental and research applications.  To accomplish this we leveraged a few pre-established technologies; namely, a piece of network virtualization/SDN creation software called Mininet (http://www.mininet.org) and Google's message serialization format/software known as Protocol Buffers (https://developers.google.com/protocol-buffers/).  Both of these projects are mature and have active developer and user communities.

Mininet:
The choice of python3 theoretically allows the usage of our code on a variety of hardware and operating system platforms but it should be noted that our entire codebase was written with the assumption that our software will be run within a mininet virtual host.  We chose to integrate mininet into our project because it allows a vast amount of control over almost every aspect of the virtual network that our application will run in (i.e. topology, link characteristics/state, traffic flow characteristics, etc...).  This is very desirable for a number of reasons, chief among those are the research and experimental ones.

Google Protocol Buffers:
The Protocol Buffers were instrumental in preventing language and hardware dependence issues from hindering our application's usefulness.  By using Protocol Buffers, other Raft implementations written in other languages and running on many different kinds of hardware can communicate with our implementation through a common interface.

Our final product for this two-semester long capstone project is five of our Raft instances running on five separate mininet instances each running on a separate Raspberry Pi.  There were a few road blocks that we had to overcome to make this possible.  The largest was how to get all five mininet instances to communicate with each other and route packets to and from the proper hosts.  To accomplish this we utilized mininet's remote controller functionality and a series of GRE tunnels to bridge the virtual and physcial networks.  Mininet allows the user to specify a remote IP address and port number to route all of its SDN controller communication to and from.  This allowed all five mininet instances to form a single, unified virtual network as well as allowing them to route virtual packets from one virtual host to another.  All that was left to do was to set up a bridge between each virtual interface and the local hardware interface.  Because we use the Open vSwitch reference controller as our SDN controller we were able to set up a GRE tunnel bridge for this purpose.  This allowed the reference controller to pass its virtual packets to the operating system for routing through the physical network from one Pi to another.  We belive that this setup can be easily extrapolated to a large number of other physical and/or virtual network circumstances.

If you would like more information about how we combined mininet and GRE tunnels check out the excellent tutorials on Tech and Trains by Gregory Gee that we based our work off of below:

Part 1: https://techandtrains.com/2013/09/11/connecting-two-mininet-networks-with-gre-tunnel/
Part 2: https://techandtrains.com/2014/01/20/connecting-two-mininet-networks-with-gre-tunnel-part-2/
Part 3: https://techandtrains.com/2014/01/25/using-linux-gre-tunnels-to-connect-two-mininet-networks/

## Getting Started
  
Below are the instructions for running Raft-Capstone.

### Prerequisites

Setting up a network emulator, for example Mininet (version 2.0 and higher), and installing python3 Google Protocol Buffers v3.1, are required before running our implementation of the Raft Algorithm.

Links for instructions to set up both Mininet and Google Protocol Buffers can be found below:

Mininet:  

http://mininet.org/download/


Google's Protocol Buffers README: 
 
https://github.com/google/protobuf

### Running Raft

Once you have the pre-requisites set up, you can then clone the current repository and begin adding the IP addresses and port numbers of the many virtual hosts you plan to create to the host list "nodeaddrs.txt". 
 
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
