import zmq
import threading

def start_broker():
    context = zmq.Context()

    # Dirección IP del Broker 1
    broker_ip = "10.43.101.52"

    # Socket para recibir de los publicadores
    frontend = context.socket(zmq.XSUB)
    frontend.bind(f"tcp://{broker_ip}:5559")

    # Socket para enviar a los suscriptores
    backend = context.socket(zmq.XPUB)
    backend.bind(f"tcp://{broker_ip}:5560")

    zmq.proxy(frontend, backend)

if __name__ == "__main__":
    print("Broker 1 iniciado...")
    start_broker()
