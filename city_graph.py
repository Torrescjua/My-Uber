from node import Node 

class CityGraph:
    def __init__(self, n, m):
        """Initialize the city grid as a graph with n rows and m columns."""
        self.n = n
        self.m = m
        self.nodes = {}  # Dictionary to store the nodes, keys are (x, y) positions
        self.build_graph()

    def build_graph(self):
        """Build the city grid as a graph where each node represents an intersection."""
        for x in range(self.n):
            for y in range(self.m):
                self.nodes[(x, y)] = Node(x, y)

        # Connect nodes to their neighbors
        for x in range(self.n):
            for y in range(self.m):
                current_node = self.nodes[(x, y)]
                # Add neighbors (up, down, left, right if within bounds)
                if x > 0:  # Up
                    current_node.add_neighbor(self.nodes[(x - 1, y)])
                if x < self.n - 1:  # Down
                    current_node.add_neighbor(self.nodes[(x + 1, y)])
                if y > 0:  # Left
                    current_node.add_neighbor(self.nodes[(x, y - 1)])
                if y < self.m - 1:  # Right
                    current_node.add_neighbor(self.nodes[(x, y + 1)])

    def get_node(self, x, y):
        """Return the node at position (x, y)."""
        return self.nodes.get((x, y), None)

    def display_graph(self):
        """Display the nodes and their connections."""
        for (x, y), node in self.nodes.items():
            neighbors = [neighbor.get_position() for neighbor in node.neighbors]
            print(f"Node ({x}, {y}) has neighbors: {neighbors}")
            
if __name__ == "__main__":
    city_graph = CityGraph(n=2, m=3) 
    city_graph.display_graph()

