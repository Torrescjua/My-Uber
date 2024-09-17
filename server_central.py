import zmq
from db_manager import DBManager  # Import the database manager

class CentralServer:
    def __init__(self, db):
        self.db = db  # Conexión a la base de datos

    def receive_positions(self):
        """Recibir posiciones de taxis a través de ZeroMQ y actualizar la base de datos."""
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.bind("tcp://*:5556")
        
        # Suscribirse a todos los mensajes de taxis
        socket.setsockopt_string(zmq.SUBSCRIBE, "Taxi")

        while True:
            message = socket.recv_string()
            print(f"Posición recibida: {message}")
            taxi_id, x, y = self.process_message(message)

            # Actualizar la posición del taxi en la base de datos
            self.db.update_taxi_position(taxi_id, x, y)

            print(f"Taxis actualizados en la base de datos: Taxi {taxi_id} está en ({x}, {y})")

    def process_message(self, message):
        """Procesar el mensaje recibido para extraer taxi_id, x, y."""
        print(f"Mensaje crudo: {message}")  # Imprimir para depurar el formato del mensaje

        # Asumimos que el mensaje tiene el formato 'Taxi <id> en la posición (<x>, <y>)'
        parts = message.split()  # Dividir por espacios
        taxi_id = int(parts[1])  # Extraer el ID del taxi

        # Encontrar la posición, que está entre paréntesis, en el último elemento del mensaje
        position_str = message[message.find("("):message.find(")") + 1]

        print(f"Cadena de posición: {position_str}")  # Debug para la cadena de posición

        if position_str.startswith('(') and position_str.endswith(')'):
            # Quitar los paréntesis y dividir la posición en x e y
            position_str = position_str[1:-1]  # Eliminar '(' y ')'
            position = position_str.split(',')

            if len(position) != 2:
                raise ValueError(f"Formato de posición no válido: {position_str}")

            # Convertir a enteros
            x, y = int(position[0].strip()), int(position[1].strip())
            return taxi_id, x, y
        else:
            raise ValueError(f"La parte de la posición del mensaje no está correctamente formateada: {position_str}")



    def assign_taxi(self, user_position):
        """Asignar el taxi más cercano a la posición del usuario."""
        taxis = self.db.get_all_taxis()

        nearest_taxi = None
        shortest_distance = float('inf')

        for taxi in taxis:
            taxi_id, x, y = taxi
            distance = abs(user_position[0] - x) + abs(user_position[1] - y)  # Distancia de Manhattan
            if distance < shortest_distance:
                shortest_distance = distance
                nearest_taxi = (taxi_id, x, y)

        if nearest_taxi:
            print(f"Taxi {nearest_taxi[0]} asignado al usuario.")
            return nearest_taxi
        else:
            print("No hay taxis disponibles.")
            return None

if __name__ == "__main__":
    db = DBManager()  # Crear la conexión a la base de datos
    server = CentralServer(db=db)
    
    try:
        server.receive_positions()  # Escuchar las posiciones de los taxis
    finally:
        db.close()  # Cerrar la conexión a la base de datos
