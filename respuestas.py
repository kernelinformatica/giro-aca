import pyodbc
from datetime import datetime
from apiclient import APIClient
from conn.DBConnection import DBConnection as DBConnection
import zeep
import xml.etree.ElementTree as ET
from requests import Session
from zeep.transports import Transport
import urllib3
from datetime import datetime, timedelta
# Suppress only the single InsecureRequestWarning from urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests




class GrabaRespuestas(DBConnection):

    def __init__(self):
        super().__init__()
        self.config = []
        self.resp = []
        fechaHoraHoyTemp = datetime.now()
        formatoFechaHoy = "%Y-%m-%d %H:%M:%S"
        self.fechaHoraHoy = fechaHoraHoyTemp.strftime(formatoFechaHoy)
        self.hoy = datetime.now()


    def grabarRespuesta(self, codigo, respuesta, nroTicket, nroCarta,  idOperacion, operacion, operador, entradaSalidas, idLlamada, descripcion, tipo):
        try:
            cursor = self.conn.cursor()
            sqlUpd = "update giro_respuesta_ws set borradoLogico = 1 where operador = '"+str(operador)+"'"
            cursor.execute(sqlUpd)
            sql=("INSERT INTO DBA.giro_respuesta_ws ( codigo, respuesta, nroTicket, nroCarta, fechaHora, idOperacion, operacion, operador, borradoLogico, entradaSalida, control, idLlamada, descripcion, tipo)"
                 " VALUES ('"+str(codigo)+"', '"+str(respuesta)+"', '"+str(nroTicket)+"', '"+str(nroCarta)+"', NOW(), '"+str(idOperacion)+"', '"+str(operacion)+"', '"+str(operador)+"', '0', '"+str(entradaSalidas)+"', NOW(), '"+str(idLlamada)+"', '"+str(descripcion)+"', '"+str(tipo)+"')")
            cursor.execute(sql)
            self.conn.commit()
        except pyodbc.Error as ex:
            print("Error al grabar la respuesta: " + str(ex))
        finally:
            cursor.close()
            self.conn.close()
           # print("Error: se ha grabado la respuesta con éxito")



