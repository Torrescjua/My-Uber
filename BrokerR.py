import zmq

def main():
    context = zmq.Context()

    # Socket frontend para recibir mensajes de los taxis
    frontend = context.socket(zmq.SUB)
    frontend.bind("tcp://*:5558")  # Broker de respaldo, diferente puerto
    frontend.setsockopt_string(zmq.SUBSCRIBE, '')

    # Socket backend para enviar mensajes al servidor central
    backend = context.socket(zmq.PUB)
    backend.bind("tcp://*:5559")  # Broker de respaldo, diferente puerto

    try:
        print("Broker de respaldo en ejecución...")
        zmq.proxy(frontend, backend)
    except Exception as e:
        print(f"Error en el proxy: {e}")
    finally:
        frontend.close()
        backend.close()
        context.term()

if __name__ == "__main__":
    main()
