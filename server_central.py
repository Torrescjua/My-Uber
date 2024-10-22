import zmq
from db_manager import DBManager 

class CentralServer:
    def __init__(self, db):
        self.db = db  # Conexión a la base de datos
        self.taxi_ips = {}  # Diccionario para almacenar la IP de cada taxi

    def receive_positions(self):
        """Recibir posiciones de taxis a través de ZeroMQ y actualizar la base de datos."""
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.bind("tcp://*:5556")
        
        # Suscribirse a todos los mensajes de taxis
        socket.setsockopt_string(zmq.SUBSCRIBE, "Taxi")

        while True:
            try:
                message = socket.recv_string()
                print(f"Posición recibida: {message}")
                taxi_id, x, y, taxi_ip = self.process_message(message)

                # Guardar la IP del taxi
                self.taxi_ips[taxi_id] = taxi_ip

                # Actualizar la posición del taxi en la base de datos
                self.db.update_taxi_position(taxi_id, x, y)

                print(f"Taxis actualizados en la base de datos: Taxi {taxi_id} está en ({x}, {y})")

                # Intentar asignar un taxi (simulación FIFO)
                self.assign_taxi()

            except KeyboardInterrupt:
                print("Servicio central detenido.")
                break

    def process_message(self, message):
        """Procesar el mensaje recibido para extraer taxi_id, x, y, y la IP."""
        print(f"Mensaje crudo: {message}")  # Imprimir para depurar el formato del mensaje

        # Asumimos que el mensaje tiene el formato 'Taxi <id> en la posición (<x>, <y>), IP: <ip>'
        parts = message.split()  # Dividir por espacios
        taxi_id = int(parts[1])  # Extraer el ID del taxi

        # Encontrar la posición, que está entre paréntesis
        position_str = message[message.find("("):message.find(")") + 1]

        print(f"Cadena de posición: {position_str}")  # Debug para la cadena de posición

        if position_str.startswith('(') and position_str.endswith(')'):
            # Quitar los paréntesis y dividir la posición en x e y
            position_str = position_str[1:-1]
            position = position_str.split(',')

            if len(position) != 2:
                raise ValueError(f"Formato de posición no válido: {position_str}")

            x, y = int(position[0].strip()), int(position[1].strip())
            
            # Extraer la IP que está después de 'IP: '
            ip_part = message.split("IP: ")[1].strip()
            print(f"IP del taxi: {ip_part}")
            
            return taxi_id, x, y, ip_part
        else:
            raise ValueError(f"La parte de la posición del mensaje no está correctamente formateada: {position_str}")

    def assign_taxi(self):
        """Asignar el primer taxi disponible siguiendo el principio FIFO."""
        taxis = self.db.get_all_taxis()

        # Imprimir los taxis disponibles para depuración
        print("Lista de taxis obtenidos de la base de datos:")
        for taxi in taxis:
            print(taxi)

        nearest_taxi = None

        # Buscar el primer taxi disponible que no esté ocupado
        for taxi in taxis:
            taxi_id, x, y, status = taxi
            if status == 'available':
                nearest_taxi = (taxi_id, x, y)
                break
            
        if nearest_taxi:
            taxi_id = nearest_taxi[0]
            print(f"Taxi {taxi_id} asignado al usuario (FIFO).")
            
            # Cambiar el estado del taxi a 'busy'
            self.db.update_taxi_status(taxi_id, 'busy')

            # Notificar al taxi que ha sido asignado
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
            socket.connect(f"tcp://{taxi_ip}:5557")  # El taxi debe estar escuchando en este puerto

            message = f"Taxi {taxi_id}, estás ocupado."
            socket.send_string(message)
            print(f"Notificación enviada a Taxi {taxi_id} en {taxi_ip}: {message}")
        else:
            print(f"No se encontró la IP del taxi {taxi_id}.")

if __name__ == "__main__":
    db = DBManager()  # Crear la conexión a la base de datos
    server = CentralServer(db=db)
    
    try:
        server.receive_positions()  # Escuchar las posiciones de los taxis
    finally:
        db.close()  # Cerrar la conexión a la base de datos
