import threading

import zmq
import time
from db_manager import DBManager

class CentralServer:
    def __init__(self, db):
        self.db = db

    def receive_positions(self):
        """Recibir y procesar posiciones publicadas en el tópico 'ubicaciones'."""
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:5555")
        socket.setsockopt_string(zmq.SUBSCRIBE, "ubicacion")

        while True:
            message = socket.recv_string()
            print(f"Posición recibida: {message}")

    def handle_ip_requests(self):
        """Responder a las solicitudes de IP publicadas en el tópico 'solicitudes_ip'."""
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:5560")

        while True:
            request = socket.recv_string()
            print(f"Solicitud recibida: {request}")
            taxi_id = request.split()[1]  # extraer ID del taxi
            response = f"IP asignada para Taxi {taxi_id}: {self.db.get_ip(taxi_id)}"
            socket.send_string(response)

    def assign_service(self):
        """Asignar servicios a los taxis disponibles."""
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.bind("tcp://*:5557")

        while True:
            taxis = self.db.get_available_taxis()
            if taxis:
                taxi_id = taxis[0]  # Obtener el primer taxi disponible
                message = f"asignacion Taxi {taxi_id}: Nuevo servicio asignado"
                socket.send_string(message)
                print(f"Servicio asignado al Taxi {taxi_id}")
                time.sleep(10)
            else:
                print("No hay taxis disponibles.")
                time.sleep(5)

if __name__ == "__main__":
    db = DBManager()

    server = CentralServer(db=db)

    try:
        position_thread = threading.Thread(target=server.receive_positions)
        position_thread.start()

        ip_thread = threading.Thread(target=server.handle_ip_requests)
        ip_thread.start()

        service_thread = threading.Thread(target=server.assign_service)
        service_thread.start()

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Servidor detenido.")
