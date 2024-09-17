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
        # Comenzar en un nodo aleatorio dentro de la ciudad
        self.current_node = city_graph.get_node(random.randint(0, city_graph.n - 1),
                                                random.randint(0, city_graph.m - 1))
        # Insertar el taxi en la base de datos con la posición inicial y obtener el taxi_id generado
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
            # Actualizar la posición del taxi en la base de datos
            self.db.update_taxi_position(self.taxi_id, self.current_node.x, self.current_node.y)
        print(f"Taxi {self.taxi_id} se movió a {self.current_node.get_position()}")

    def get_position(self):
        """Obtener la posición actual del taxi."""
        return self.current_node.get_position()

    def publish_position(self):
        """Publicar la posición del taxi en el servidor central usando ZeroMQ."""
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.connect("tcp://localhost:5556")


        while True:
            self.move()  # Mover el taxi a una nueva posición
            message = f"Taxi {self.taxi_id} en la posición {self.get_position()}, IP: {self.local_ip}"
            print(f"Publicando: {message}")
            socket.send_string(message)
            time.sleep(2)
            
    def listen_for_assignment(self):
        """Escuchar asignaciones del servidor central usando ZeroMQ."""
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(f"tcp://{self.local_ip}:5557")  # El taxi escucha en su propio puerto
        socket.setsockopt_string(zmq.SUBSCRIBE, f"Taxi {self.taxi_id}")

        print(f"Taxi {self.taxi_id} está esperando asignaciones...")

        while True:
            message = socket.recv_string()
            print(f"Asignación recibida por Taxi {self.taxi_id}: {message}")
            # Aquí puedes agregar lógica para procesar la asignación recibida


if __name__ == "__main__":
    city_graph = CityGraph(n=8, m=10)  # Crear un gráfico de la ciudad
    db = DBManager()  # Crear una conexión con la base de datos PostgreSQL

    taxi = Taxi(city_graph=city_graph, db=db)

    try:
        # Crear un hilo para publicar la posición del taxi
        position_thread = threading.Thread(target=taxi.publish_position)
        position_thread.daemon = True  # Hilo daemon
        position_thread.start()

        # Crear un hilo para escuchar las asignaciones del servidor central
        listen_thread = threading.Thread(target=taxi.listen_for_assignment)
        listen_thread.daemon = True  # Hilo daemon
        listen_thread.start()

        # Mantener el programa principal corriendo
        while True:
            time.sleep(1)  # El programa principal permanece activo

    except KeyboardInterrupt:
        print("Servicio detenido manualmente.")
    finally:
        # Cambiar el estado del taxi a 'inactive' antes de cerrar
        db.update_taxi_status(taxi.taxi_id, 'inactive')
        db.close()


