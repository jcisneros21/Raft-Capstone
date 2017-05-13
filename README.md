# Raft-Capstone
This is the alpha version of our CSCI 4962 capstone project.  We are seniors at Saint Louis University working with Dr. Flavio Esposito on developing our own version of the Raft consensus protocol. Below is an explanation of what our project is and how it works.

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

For Google Protocol Buffers, you must install the the protocol compiler and the python runtime libraries in the environment that you plan to install Mininet. The version of Google Protocol Buffers that you will need to download is v3.1. You can find the zip file for downloading here:  

https://github.com/google/protobuf/releases

You have the choice of downloading the pre-compiled binary version of Google Protocol Buffers, which is the zip file that is named protoc-3.1.0-linux-x86, and installing the python runtime libraries afterwards. This is the fastest route and If you decide to take it, you must enter into the downloaded directory and place the binary protoc file that is located in the bin directory into your PATH variable. From here you can download the protobuf-python tar or zip file and follow the installation instructions from the README.md located in the python directory.  

Otherwise, you can download the protobuf-python tar or zip file and install the protoc compiler and python runtime libraries from there. This will take a little longer as you have to wait for the installation to be completed. The directions for this process is in the README.md file that is located in the src directory. 

### Running Raft

Once you have the pre-requisites set up, you can then clone the current repository to the environment with Mininet and begin adding the IP addresses and port numbers of the many virtual hosts you plan to create to our host list "nodeaddrs.txt".

Already we include the standard of five hosts with their IP address, port number and their specified log file. Each IP address in the host list corresponds to what Mininet already sets up when creating a host. If you would like to add another host to the host list, please append the following line to the end of file.  
```
[IP address],[Port Number],[logfile(# of host).txt] 
```
For information regarding commands in Mininet, please visit the link below:  

http://mininet.org/walkthrough/#interact-with-hosts-and-switches

To get started to initialize five virtual hosts in Mininet, you can use the command:
```
sudo mn –topo single,5
```

Just to make sure everything has went well, ping all five hosts with the command  
```
pingall
```

in the Mininet terminal. This will tell us if a virtual host is not able to communicate with other hosts in the virtual network. If not, there may have been some issues when Mininet was initialized or when installing Mininet. 

Once all five virtual hosts can communicate with each other, you can open separate terminals for each host using the command:
```
xterm h1 h2 h3 h4 h5
```

Now, please run a instance of our implementation of the Raft Algorithm on each terminal with the command:
```
python3 test.py
```
Raft is now running!

### Features

#### Leader Elections

Once you have initialized an instance of our Raft algorithm on each virtual host, they will began a process called Leader Election. In this phase, one instance of Raft will try to become Leader. You will know if a instance has become a leader by the terminal that outputs “New Leader state, Term #2”. Another indicator is if the terminal is no longer outputting the Election Timeout Value.

#### Requests
You can start appending request via the Leader’s terminal. Once you are on the Leader’s terminal, write any given string and press enter. The leader will take that string and wrap it with a Log Entry message to start the consensus process of Raft. Eventually, if a majority hosts are running the instance of Raft, the log message will be committed and a consensus has been reached.

#### Output the entries inside a Log
If you want to see a log of a given instance of Raft, use the command:  
```
printlog
```

#### Stopping an instance of Raft
You can stop a given instance of Raft with the command:
```
quit
```

#### Dynamic Host List
You no longer need to continue to add another host by appending it to the host list. If the network information of a host in not on the global host list, you can just start up the instance of Raft and it will contact the system that is currently running by host list. That requested instance will eventually become added to the global host list and the Leader will preform the operations for node recovery. 


## Authors

* **Fred Trelz**
* **Jessie Cisneros**
