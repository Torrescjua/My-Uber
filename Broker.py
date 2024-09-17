import zmq

def main():
    context = zmq.Context()

    # Socket frontend para recibir mensajes de los taxis (publicadores)
    frontend = context.socket(zmq.SUB)
    frontend.bind("tcp://*:5555")  # Cambiar puerto según sea necesario
    frontend.setsockopt_string(zmq.SUBSCRIBE, '')

    # Socket backend para enviar mensajes al servidor central (suscriptor)
    backend = context.socket(zmq.PUB)
    backend.bind("tcp://*:5556")  # Cambiar puerto según sea necesario

    # Establecer proxy para redirigir mensajes del frontend al backend
    try:
        print("Broker en ejecución...")
        zmq.proxy(frontend, backend)
    except Exception as e:
        print(f"Error en el proxy: {e}")
    finally:
        frontend.close()
        backend.close()
        context.term()

if __name__ == "__main__":
    main()
