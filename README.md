# My-Uber
Este proyecto simula un sistema distribuido de taxis en tiempo real. Los taxis publican su ubicación mediante ZeroMQ, y un servidor central recibe las posiciones y las almacena en una base de datos PostgreSQL. Además, el sistema asigna el taxi más cercano a los usuarios, demostrando la interacción entre servicios distribuidos en Python.

## Características

- **Sistema distribuido** utilizando ZeroMQ para la comunicación.
- **Almacenamiento de datos** en una base de datos PostgreSQL.
- **Asignación de taxis** más cercanos a los usuarios mediante la distancia de Manhattan.
- **Simulación de movimiento de taxis** y actualización de sus posiciones en tiempo real.
- **Creación automática de la base de datos** si no existe.

## Estructura del Proyecto

- **taxi.py**: Simula el movimiento de un taxi dentro de una ciudad y publica su posición en tiempo real a través de ZeroMQ.
- **server_central.py**: Recibe las posiciones de los taxis a través de ZeroMQ y actualiza sus posiciones en la base de datos.
- **db_manager.py**: Gestiona la conexión y las interacciones con la base de datos PostgreSQL, incluyendo la creación de la base de datos y las tablas.
- **city_graph.py**: Representa el mapa de la ciudad, modelando los nodos y las conexiones entre ellos (asumido, dado que no se ha proporcionado el código completo).
- **requirements.txt**: Archivo que contiene las dependencias del proyecto.
- **README.md**: Este archivo de documentación.

## Requisitos

### Software

- **Python 3.x**
- **PostgreSQL** (Versión 12 o superior recomendada)
- **ZeroMQ**

### Dependencias

Las dependencias de Python están listadas en el archivo `requirements.txt`. Para instalarlas, usa:

```bash
pip install -r requirements.txt
