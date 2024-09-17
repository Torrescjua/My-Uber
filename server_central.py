import zmq
import time
from db_manager import DBManager

class CentralServer:
    def __init__(self, db):
        self.db = db
        self.taxi_ips = {}

    def receive_positions(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)

        # Conectar inicialmente al broker principal
        connected = self.connect_to_broker(socket, "tcp://localhost:5556", "tcp://localhost:5559")

        if not connected:
            print("No se pudo conectar ni al broker principal ni al de respaldo. Terminando.")
            return

        # Suscribirse a todos los mensajes de taxis
        socket.setsockopt_string(zmq.SUBSCRIBE, "Taxi")

        while True:
            try:
                message = socket.recv_string()
                print(f"Posición recibida: {message}")
                taxi_id, x, y, taxi_ip = self.process_message(message)

                self.taxi_ips[taxi_id] = taxi_ip
                self.db.update_taxi_position(taxi_id, x, y)
                print(f"Taxis actualizados en la base de datos: Taxi {taxi_id} está en ({x}, {y})")
                self.assign_taxi()

            except zmq.ZMQError as e:
                print(f"Error en la comunicación: {e}")
                # Intentar reconectar si se pierde la conexión
                connected = self.connect_to_broker(socket, "tcp://localhost:5556", "tcp://localhost:5559")
                if not connected:
                    print("No se pudo reconectar a ningún broker. Terminando.")
                    break
            except KeyboardInterrupt:
                print("Servicio central detenido.")
                break

    def connect_to_broker(self, socket, broker_main, broker_backup):
        """Intentar conectar al broker principal y luego al de respaldo si el primero falla."""
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

    def process_message(self, message):
        """Procesar el mensaje recibido para extraer taxi_id, x, y, y la IP."""
        print(f"Mensaje crudo: {message}")

        parts = message.split()
        taxi_id = int(parts[1])

        position_str = message[message.find("("):message.find(")") + 1]

        print(f"Cadena de posición: {position_str}")

        if position_str.startswith('(') and position_str.endswith(')'):
            position_str = position_str[1:-1]
            position = position_str.split(',')
            if len(position) != 2:
                raise ValueError(f"Formato de posición no válido: {position_str}")

            x, y = int(position[0].strip()), int(position[1].strip())
            ip_part = message.split("IP: ")[1].strip()
            print(f"IP del taxi: {ip_part}")
            return taxi_id, x, y, ip_part
        else:
            raise ValueError(f"La parte de la posición del mensaje no está correctamente formateada: {position_str}")

    def assign_taxi(self):
        """Asignar el primer taxi disponible siguiendo el principio FIFO."""
        taxis = self.db.get_all_taxis()
        print("Lista de taxis obtenidos de la base de datos:")
        for taxi in taxis:
            print(taxi)

        nearest_taxi = None
        for taxi in taxis:
            taxi_id, x, y, status = taxi
            if status == 'available':
                nearest_taxi = (taxi_id, x, y)
                break

        if nearest_taxi:
            taxi_id = nearest_taxi[0]
            print(f"Taxi {taxi_id} asignado al usuario (FIFO).")
            self.db.update_taxi_status(taxi_id, 'busy')
            self.notify_taxi(taxi_id)
            return nearest_taxi
        else:
            print("No hay taxis disponibles.")
            return None

    def notify_taxi(self, taxi_id):
        """Enviar una notificación al taxi asignado de que está ocupado."""
        if taxi_id in self.taxi_ips:
            taxi_ip = self.taxi_ips[taxi_id]
            context = zmq.Context()
            socket = context.socket(zmq.PUB)
            socket.connect(f"tcp://{taxi_ip}:5557")

            message = f"Taxi {taxi_id}, estás ocupado."
            socket.send_string(message)
            print(f"Notificación enviada a Taxi {taxi_id} en {taxi_ip}: {message}")
        else:
            print(f"No se encontró la IP del taxi {taxi_id}.")

if __name__ == "__main__":
    db = DBManager()
    server = CentralServer(db=db)

    try:
        server.receive_positions()
    finally:
        db.close()
