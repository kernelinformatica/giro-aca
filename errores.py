import pyodbc
from conn.DBConnection import DBConnection as DBConnection
import urllib3
from datetime import datetime, timedelta
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)





class GrabaErrores(DBConnection):

    def __init__(self):
        super().__init__()
        self.config = []
        self.resp = []
        fechaHoraHoyTemp = datetime.now()
        formatoFechaHoy = "%Y-%m-%d %H:%M:%S"
        self.fechaHoraHoy = fechaHoraHoyTemp.strftime(formatoFechaHoy)
        self.hoy = datetime.now()


    def grabarError(self, errorCodigo, errorDescripcion, nroTicket, nroCarta, fechaHora, idOperacion, operacion, operador, entradaSalida, planta, idLlamada):
        try:
            cursor = self.conn.cursor()
            sqlUpd = "update giro_errores_ws set borradoLogico = 1 where operador = '"+str(operador)+"'"
            cursor.execute(sqlUpd)
            sql="INSERT INTO DBA.giro_errores_ws ( errorCodigo, errorDescripcion, nroTicket, nroCarta, fechaHora, idOperacion,  operacion, operador, borradoLogico, entradaSalida, control, planta, idLlamada) VALUES ('"+str(errorCodigo)+"', '"+str(errorDescripcion)+"', '"+str(nroTicket)+"', '"+str( nroCarta)+"', '"+str(fechaHora)+"', '"+str(idOperacion)+"', '"+str(operacion)+"', '"+str(operador)+"', '0', '"+str(entradaSalida)+"', NOW(), '"+str(planta)+"', '"+str(idLlamada)+"')"
            cursor.execute(sql)
            self.conn.commit()
        except pyodbc.Error as ex:
            print("Error al grabar error: " + str(ex))
        finally:
            cursor.close()
            self.conn.close()
            print("Error: se ha generado un error en la operación")



