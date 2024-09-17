import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

class DBManager:
    def __init__(self):
        """Initialize the connection to the PostgreSQL database."""
        # Cargar las variables de entorno
        load_dotenv()

        # Intentar conectarse a la base de datos especificada en las variables de entorno
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=os.getenv("DB_PORT", "5432")
            )
            self.cursor = self.conn.cursor()
            print(f"Conexión exitosa a la base de datos '{os.getenv('DB_NAME')}'")
        except psycopg2.OperationalError:
            print(f"La base de datos '{os.getenv('DB_NAME')}' no existe. Creándola ahora...")
            self.create_database()
            # Conectar de nuevo, ahora que la base de datos ha sido creada
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=os.getenv("DB_PORT", "5432")
            )
            self.cursor = self.conn.cursor()
            print(f"Conexión exitosa a la base de datos '{os.getenv('DB_NAME')}' después de la creación.")
            self.create_tables()

    def create_database(self):
        """Create the database if it does not exist."""
        # Conectar a la base de datos 'postgres', que siempre existe
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database="postgres",
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432")
        )
        conn.autocommit = True  # Necesario para ejecutar la creación de la base de datos
        cursor = conn.cursor()

        # Crear la base de datos usando una consulta SQL
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(os.getenv("DB_NAME"))
        ))

        print(f"Base de datos '{os.getenv('DB_NAME')}' creada exitosamente.")
        cursor.close()
        conn.close()

    def create_tables(self):
        """Create necessary tables if they don't exist."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS taxis (
                taxi_id SERIAL PRIMARY KEY,
                x INTEGER,
                y INTEGER,
                status TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                service_id SERIAL PRIMARY KEY,
                taxi_id INTEGER,
                start_position TEXT,
                end_position TEXT,
                FOREIGN KEY(taxi_id) REFERENCES taxis(taxi_id)
            )
        ''')
        self.conn.commit()

    def add_taxi(self, x, y, status="available"):
        """Insert a taxi into the database and return the generated taxi_id."""
        self.cursor.execute('''
            INSERT INTO taxis (x, y, status)
            VALUES (%s, %s, %s)
            RETURNING taxi_id
        ''', (x, y, status))
        taxi_id = self.cursor.fetchone()[0]
        self.conn.commit()
        return taxi_id

    def update_taxi_position(self, taxi_id, x, y):
        """Update the position of a taxi in the database."""
        self.cursor.execute('''
            UPDATE taxis
            SET x = %s, y = %s
            WHERE taxi_id = %s
        ''', (x, y, taxi_id))
        self.conn.commit()

    def get_taxi_position(self, taxi_id):
        """Retrieve the position of a specific taxi."""
        self.cursor.execute('''
            SELECT x, y FROM taxis WHERE taxi_id = %s
        ''', (taxi_id,))
        return self.cursor.fetchone()

    def update_taxi_status(self, taxi_id, status):
        """Update the status of a taxi in the database (active, inactive, deleted)."""
        self.cursor.execute('''
            UPDATE taxis
            SET status = %s
            WHERE taxi_id = %s
        ''', (status, taxi_id))
        self.conn.commit()
        print(f"Estado del taxi {taxi_id} actualizado a {status}")
        
    def get_all_taxis(self):
        """Obtener todos los taxis de la base de datos con su posición y estado."""
        self.cursor.execute('''
            SELECT taxi_id, x, y, status
            FROM taxis
        ''')
        taxis = self.cursor.fetchall()
        return taxis

    def close(self):
        """Close the connection to the database."""
        self.conn.close()
