from psycopg2 import connect

class Config:
    SECRET_KEY = 'B!1w8NAt1T^%kvhUI*S^'
    UPLOAD_FOLDER = 'static/uploads'

class DevelopmentConfig(Config):
    DEBUG = True

config = {
    'development': DevelopmentConfig
}

HOST = 'localhost'
PORT = '5432'
BD = 'trabajo_final'
USUARIO = 'postgres'
PASSWORD = 'pass'


def EstablecerConexion():
    try:
        conexion = connect(host=HOST, port=PORT, dbname=BD, user=USUARIO, password=PASSWORD)
    except ConnectionError:
        print('Error de conexión')
    return conexion