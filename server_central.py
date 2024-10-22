import zmq
from db_manager import DBManager

class CentralServer:
    def __init__(self, db):
        self.db = db
        self.taxi_ips = {}

    def receive_positions(self):
        """Recibir posiciones de taxis desde múltiples Brokers usando ZeroMQ con tópicos."""
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

        # Suscribirse a las posiciones de todos los taxis utilizando un patrón de tópicos
        socket.setsockopt_string(zmq.SUBSCRIBE, "taxi.")

        while True:
            try:
                # Recibir mensaje con tópico incluido
                message = socket.recv_string()
                print(f"Posición recibida: {message}")

                # El mensaje incluye el tópico (taxi.<taxi_id>.position)
                topic, data = message.split(maxsplit=1)
                taxi_id = self.extract_taxi_id(topic)
                x, y, taxi_ip = self.process_message(data)

                self.taxi_ips[taxi_id] = taxi_ip
                self.db.update_taxi_position(taxi_id, x, y)
                print(f"Taxis actualizados en la base de datos: Taxi {taxi_id} está en ({x}, {y})")

                self.assign_taxi()

            except KeyboardInterrupt:
                print("Servicio central detenido.")
                break

    def extract_taxi_id(self, topic):
        """Extraer el taxi_id del tópico."""
        # Suponiendo que el tópico es de la forma 'taxi.<taxi_id>.position'
        try:
            _, taxi_id_str, _ = topic.split('.')
            taxi_id = int(taxi_id_str)
            return taxi_id
        except ValueError as e:
            raise ValueError(f"Formato de tópico no válido: {topic}") from e

    def process_message(self, message):
        """Procesar el mensaje recibido para extraer x, y, y la IP."""
        # Extraer la posición
        try:
            position_str = message[message.find("("):message.find(")") + 1]
            if position_str.startswith('(') and position_str.endswith(')'):
                position_str = position_str[1:-1]
                position = position_str.split(',')
                x, y = int(position[0].strip()), int(position[1].strip())
            else:
                raise ValueError(f"Formato de posición no válido: {position_str}")

            # Extraer la IP
            ip_index = message.find("IP: ")
            if ip_index != -1:
                taxi_ip = message[ip_index + 4:].strip()
            else:
                raise ValueError("IP no encontrada en el mensaje.")

            return x, y, taxi_ip
        except Exception as e:
            raise ValueError(f"Error al procesar el mensaje: {message}") from e

    def assign_taxi(self):
        """Asignar el primer taxi disponible."""
        taxis = self.db.get_all_taxis()
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

    def notify_taxi(self, taxi_id):
        """Enviar una notificación al taxi asignado usando tópicos."""
        context = zmq.Context()
        socket = context.socket(zmq.PUB)

        # Lista de direcciones de los Brokers
        broker_addresses = [
            "tcp://localhost:5559",  # Primer Broker
            "tcp://localhost:5561"   # Segundo Broker (redundante)
        ]

        # Conectar a todos los Brokers
        for broker in broker_addresses:
            socket.connect(broker)

        # Publicar el mensaje de asignación en el tópico correspondiente al taxi
        topic = f"taxi.{taxi_id}.assignment"
        message = f"Taxi {taxi_id}, has sido asignado a un servicio."

        print(f"Notificación enviada en tópico '{topic}': {message}")
        socket.send_string(f"{topic} {message}")

if __name__ == "__main__":
    db = DBManager()
    server = CentralServer(db=db)

    try:
        server.receive_positions()
    finally:
        db.close()
