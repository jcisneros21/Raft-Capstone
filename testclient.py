import time
import socket
import testmessages_pb2 as protoc

talksocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
talksocket.connect(('10.0.0.1', 9000))
heartbeat = protoc.HeartbeatTest()
heartbeat.fromnode = "h2"
heartbeat.tonode = "h1"
heartbeat.message = "test message."
talksocket.send(heartbeat.SerializeToString())

