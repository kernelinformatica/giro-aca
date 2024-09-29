import pyodbc
import configparser

class DBConnection:
    def __init__(self):
        try:
            self.conn = self.create_connection()
        except pyodbc.Error as e:
            print("Error al conectar a la base de datos:", e)
            self.conn = None
        except configparser.Error as e:
            print("Error al leer el archivo de configuración:", e)
            self.conn = None

    def create_connection(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.serv = config['CONEXION']['serv']
        self.usr = config['CONEXION']['usr']
        self.passwd = config['CONEXION']['passwd']
        self.db = config['CONEXION']['db']
        self.prt = config['CONEXION']['prt']
        self.nombreCliente = config['EMPRESA']['nombre']
        self.token = config['TOKEN']['TOKEN']
        self.urlAuth = config['SERVICIOS']['urlAuth']

        conn = pyodbc.connect('DSN=' + self.serv + ';Database=' + self.db + ';UID=' + self.usr + ';PWD=' + self.passwd, autocommit=True)
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin1')
        conn.setencoding('latin1')
        return conn