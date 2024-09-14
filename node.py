class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.neighbors = []  # List to store neighboring nodes

    def add_neighbor(self, neighbor):
        """Add a neighboring node"""
        self.neighbors.append(neighbor)

    def get_position(self):
        return (self.x, self.y)
