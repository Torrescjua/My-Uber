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
        self.db = db
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
        return self.current_node.get_position()

    def publish_position(self):
        """Publicar la posición del taxi usando ZeroMQ con tolerancia a fallos."""
        context = zmq.Context()
        socket = context.socket(zmq.PUB)

        # Intentar conectarse al broker principal
        connected = self.connect_to_broker(socket, "tcp://localhost:5555", "tcp://localhost:5558")
        if not connected:
            print("No se pudo conectar ni al broker principal ni al de respaldo. Terminando.")
            return

        while True:
            try:
                self.move()
                message = f"Taxi {self.taxi_id} en la posición {self.get_position()}, IP: {self.local_ip}"
                print(f"Publicando: {message}")
                socket.send_string(message)
                time.sleep(5)
            except zmq.ZMQError as e:
                print(f"Error en la comunicación: {e}")
                connected = self.connect_to_broker(socket, "tcp://localhost:5555", "tcp://localhost:5558")
                if not connected:
                    print("No se pudo reconectar a ningún broker. Terminando.")
                    break

    def connect_to_broker(self, socket, broker_main, broker_backup):
        """Intentar conectar al broker principal y luego al de respaldo si falla."""
        max_retries = 5
        backoff_time = 1

        for attempt in range(max_retries):
            try:
                print(f"Intentando conectar al broker principal (intento {attempt + 1})")
                socket.connect(broker_main)
                print("Conectado al broker principal.")
                return True
            except zmq.ZMQError:
                print("Fallo al conectar al broker principal, intentando el de respaldo...")
                try:
                    socket.connect(broker_backup)
                    print("Conectado al broker de respaldo.")
                    return True
                except zmq.ZMQError:
                    print(f"Fallo en la reconexión. Reintentando en {backoff_time} segundos...")
                    time.sleep(backoff_time)
                    backoff_time *= 2

        print("Error: no se pudo conectar ni al broker principal ni al de respaldo.")
        return False

    def listen_for_assignment(self):
        """Escuchar asignaciones del servidor central usando ZeroMQ."""
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:5557")
        socket.setsockopt_string(zmq.SUBSCRIBE, f"Taxi {self.taxi_id}")

        print(f"Taxi {self.taxi_id} está esperando asignaciones...")

        while True:
            message = socket.recv_string()
            print(f"Asignación recibida por Taxi {self.taxi_id}: {message}")
            # Aquí puedes agregar lógica para procesar la asignación recibida


if __name__ == "__main__":
    city_graph = CityGraph(n=8, m=10)
    db = DBManager()

    taxi = Taxi(city_graph=city_graph, db=db)

    try:
        position_thread = threading.Thread(target=taxi.publish_position)
        position_thread.daemon = True
        position_thread.start()

        listen_thread = threading.Thread(target=taxi.listen_for_assignment)
        listen_thread.daemon = True
        listen_thread.start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Servicio detenido manualmente.")
    finally:
        db.update_taxi_status(taxi.taxi_id, 'inactive')
        db.close()
