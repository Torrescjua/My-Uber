import zmq
import threading

def start_broker():
    context = zmq.Context()

    # Socket que recibe de los taxis (publishers)
    frontend = context.socket(zmq.XSUB)
    frontend.bind("tcp://*:5558")  # Puerto para los taxis

    # Socket que envía hacia el servidor central (subscribers)
    backend = context.socket(zmq.XPUB)
    backend.bind("tcp://*:5559")  # Puerto para el servidor central

    # Crear un proxy que permite la comunicación entre el frontend y backend
    zmq.proxy(frontend, backend)

    # Cerrar los sockets y el contexto cuando el broker termine
    frontend.close()
    backend.close()
    context.term()

if __name__ == "__main__":
    print("Broker iniciado con threading...")

    # Crear un hilo para manejar el broker
    broker_thread = threading.Thread(target=start_broker)
    broker_thread.start()
    
    # Monitorear el estado del broker, agregar lógica aquí si es necesario
    broker_thread.join()
