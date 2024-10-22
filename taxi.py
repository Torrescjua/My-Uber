import socket
import threading
import zmq
import random
import time
from city_graph import CityGraph  
from db_manager import DBManager

class Taxi:
    def __init__(self, city_graph, db):
        self.city_graph = city_graph
        self.db = db  # Conexión a la base de datos
        self.current_node = city_graph.get_node(random.randint(0, city_graph.n - 1),
                                                random.randint(0, city_graph.m - 1))
        self.taxi_id = self.db.add_taxi(self.current_node.x, self.current_node.y)
        print(f"Taxi creado con ID: {self.taxi_id}")
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

    def get_position(self):
        """Obtener la posición actual del taxi."""
        return self.current_node.get_position()

    def publish_position(self):
        """Publicar la posición del taxi en múltiples Brokers usando ZeroMQ con tópicos."""
        context = zmq.Context()

        # Lista de direcciones de los Brokers
        broker_addresses = [
            "tcp://localhost:5559",  # Primer Broker
            "tcp://localhost:5561"   # Segundo Broker (redundante)
        ]

        socket = context.socket(zmq.PUB)

        # Conectar a todos los Brokers
        for broker in broker_addresses:
            socket.connect(broker)

        while True:
            self.move()  # Mover el taxi a una nueva posición
            
            # Tópico para publicar la posición del taxi
            topic = f"taxi.{self.taxi_id}.position"
            message = f"{self.get_position()}, IP: {self.local_ip}"
            
            print(f"Publicando en tópico '{topic}': {message}")
            socket.send_string(f"{topic} {message}")
            time.sleep(5)

    def listen_for_assignment(self):
        """Escuchar asignaciones desde los Brokers usando ZeroMQ y tópicos."""
        context = zmq.Context()
        socket = context.socket(zmq.SUB)

        # Lista de direcciones de los Brokers
        broker_addresses = [
            "tcp://localhost:5560",  # Primer Broker
            "tcp://localhost:5562"   # Segundo Broker (redundante)
        ]

        # Conectar a todos los Brokers
        for broker in broker_addresses:
            socket.connect(broker)

        # Suscribirse solo al tópico de asignaciones de este taxi
        socket.setsockopt_string(zmq.SUBSCRIBE, f"taxi.{self.taxi_id}.assignment")

        print(f"Taxi {self.taxi_id} está esperando asignaciones en el tópico 'taxi.{self.taxi_id}.assignment'...")

        while True:
            message = socket.recv_string()
            print(f"Asignación recibida por Taxi {self.taxi_id}: {message}")

if __name__ == "__main__":
    city_graph = CityGraph(n=8, m=10)
    db = DBManager()

    taxi = Taxi(city_graph=city_graph, db=db)

    try:
        # Crear un hilo para publicar la posición del taxi
        position_thread = threading.Thread(target=taxi.publish_position)
        position_thread.daemon = True
        position_thread.start()

        # Crear un hilo para escuchar las asignaciones
        listen_thread = threading.Thread(target=taxi.listen_for_assignment)
        listen_thread.daemon = True
        listen_thread.start()

        # Mantener el programa principal activo
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Servicio detenido manualmente.")
    finally:
        # Cambiar el estado del taxi a 'inactive' antes de cerrar
        db.update_taxi_status(taxi.taxi_id, 'inactive')
        db.close()
