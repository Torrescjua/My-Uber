import zmq
import threading

def start_broker():
    context = zmq.Context()

    # Socket para recibir de los publicadores
    frontend = context.socket(zmq.XSUB)
    frontend.bind("tcp://*:5561")

    # Socket para enviar a los suscriptores
    backend = context.socket(zmq.XPUB)
    backend.bind("tcp://*:5562")

    zmq.proxy(frontend, backend)

if __name__ == "__main__":
    print("Broker 2 iniciado...")
    start_broker()
