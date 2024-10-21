import threading

import zmq
import random
import socket
import time
from city_graph import CityGraph
from db_manager import DBManager


class Taxi:
    def __init__(self, city_graph, db):
        self.city_graph = city_graph
        self.db = db
        self.current_node = city_graph.get_node(random.randint(0, city_graph.n - 1),
                                                random.randint(0, city_graph.m - 1))
        self.taxi_id = self.db.add_taxi(self.current_node.x, self.current_node.y)
        self.local_ip = self.get_local_ip()

    def get_local_ip(self):
        """Obtener la IP local del taxi."""
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip

    def move(self):
        """Mover el taxi a un nodo vecino aleatorio."""
        if self.current_node and self.current_node.neighbors:
            self.current_node = random.choice(self.current_node.neighbors)
            self.db.update_taxi_position(self.taxi_id, self.current_node.x, self.current_node.y)
        print(f"Taxi {self.taxi_id} se movió a {self.current_node.get_position()}")

    def publish_position(self):
        """Publicar la posición del taxi en el tópico 'ubicaciones'."""
        context = zmq.Context()
        socket = context.socket(zmq.PUB)

        # Conectarse al broker principal o de respaldo
        socket.connect("tcp://localhost:5555")

        while True:
            self.move()
            message = f"ubicacion Taxi {self.taxi_id} ({self.current_node.x}, {self.current_node.y}), IP: {self.local_ip}"
            socket.send_string(message)
            time.sleep(5)

    def request_ip(self):
        """Solicitar la IP al servidor central en el tópico 'solicitudes_ip'."""
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://localhost:5560")

        message = f"request_ip Taxi {self.taxi_id}"
        socket.send_string(message)
        response = socket.recv_string()
        print(f"Respuesta de IP para Taxi {self.taxi_id}: {response}")

    def listen_for_service(self):
        """Escuchar asignaciones del servidor central en el tópico 'asignaciones'."""
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:5557")
        socket.setsockopt_string(zmq.SUBSCRIBE, f"asignacion Taxi {self.taxi_id}")

        while True:
            message = socket.recv_string()
            print(f"Servicio asignado a Taxi {self.taxi_id}: {message}")


if __name__ == "__main__":
    city_graph = CityGraph(n=8, m=10)
    db = DBManager()

    taxi = Taxi(city_graph=city_graph, db=db)

    # Iniciar diferentes servicios en hilos separados
    try:
        position_thread = threading.Thread(target=taxi.publish_position)
        position_thread.start()

        service_thread = threading.Thread(target=taxi.listen_for_service)
        service_thread.start()

        ip_thread = threading.Thread(target=taxi.request_ip)
        ip_thread.start()

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Servicio detenido.")
