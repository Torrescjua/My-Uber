import zmq

class CentralServer:
    def __init__(self):
        self.taxis = {}  # Dictionary to store the positions of the taxis
    
    def receive_positions(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:5556")  # Connect to the channel where taxis publish

        # Subscribe to all messages that start with "Taxi"
        socket.setsockopt_string(zmq.SUBSCRIBE, "Taxi")

        while True:
            message = socket.recv_string()
            print(f"Position received: {message}")
            # Update the dictionary of taxis
            taxi_id = int(message.split()[1])
            position = tuple(map(int, message.split()[-1][1:-1].split(',')))
            self.taxis[taxi_id] = position

            # Show the state of the registered taxis
            print(f"Registered taxis: {self.taxis}")

if __name__ == "__main__":
    server = CentralServer()
    server.receive_positions()
