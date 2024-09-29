import pyodbc
import configparser


# levanto datos de coneccion de config.ini #######
config = configparser.ConfigParser()
config.read('config.ini')
serv = config['CONEXION']['serv']
usr = config['CONEXION']['usr']
passwd = config['CONEXION']['passwd']
db = config['CONEXION']['db']
prt = config['CONEXION']['prt']
nombreCliente =config['EMPRESA']['nombre']
token = config['TOKEN']['TOKEN']
urlAuth = config['SERVICIOS']['urlAuth']

####################################################
conn = pyodbc.connect('DSN='+serv+';Database='+db+';UID='+usr+';PWD='+passwd, autocommit=True)
conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin1')
conn.setencoding('latin1')

print (":: "+str(nombreCliente)+" :: Sincronización Web ::")
print (":: Conectado a "+str(serv)+ " ::")
"""
cursor = conn.cursor()
cursor.execute("SELECT * FROM ctacte_padron")
for row in cursor.fetchall():
    print (row)
"""