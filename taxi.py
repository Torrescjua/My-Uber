import zmq
import time
import random

class Taxi:
    def __init__(self, taxi_id, n, m):
        self.taxi_id = taxi_id
        self.position = (random.randint(0, n), random.randint(0, m))
        self.n = n
        self.m = m
    
    def move(self):
        # Basic movement of the taxi (horizontal or vertical)
        x, y = self.position
        move_horizontal = random.choice([-1, 0, 1])  # Horizontal movement in X
        move_vertical = random.choice([-1, 0, 1])  # Vertical movement in Y
        
        new_position = (
            min(max(x + move_horizontal, 0), self.n),
            min(max(y + move_vertical, 0), self.m)
        )
        self.position = new_position

    def publish_position(self):
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.bind("tcp://*:5556")  # Publish address (can be a remote server)

        while True:
            self.move()
            message = f"Taxi {self.taxi_id} at position {self.position}"
            print(f"Publishing: {message}")
            socket.send_string(message)
            time.sleep(2)  # Publish every 2 seconds

if __name__ == "__main__":
    taxi = Taxi(taxi_id=1, n=10, m=10)
    taxi.publish_position()
