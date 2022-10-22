import sys
import zmq

#  Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)

print("Waiting for status")
socket.connect("tcp://localhost:5556")


socket.setsockopt_string(zmq.SUBSCRIBE, '')

# Process 5 updates
for _ in range(5):
    status = socket.recv_json()
    print(status)
