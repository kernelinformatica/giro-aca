# The common XML.RPC endpoint
import smtplib
from datetime import datetime
from email.message import EmailMessage
import xml.etree.ElementTree as ET
import zeep
from requests import Session
from zeep.transports import Transport
from conn.DBConnection import DBConnection as DBConnection
from giros_authenticate import GiroAuthenticate as GiroAuthenticate
import argparse
import errores
import respuestas
'''
Consulta de Movimientos desde Plantas 
Desde los servidores de las plantas (online/offline) se consumen los métodos 
ObtenerRegistrosGenericos y ObtenerMlogis del wsSmartFarm para obtener los movimientos
'''

class GirosObtenerRegistros(DBConnection):
    def __init__(self):
        super().__init__()
        self.config = []
        self.resp = []
        self.tokenGiro =""
        self.codigoPlanta = 0
        self.codigPlantaAfip = 0
        self.operador = "."
        self.clientFarm = self._create_soap_client_farm()
        self.hoy = datetime.now()
        self.maskCuenta = "0000000"
        self.datos = []
        self.datosParaGiro = []

    def obtenerRegistrosGenericos(self):
        print("::: obtenerRegistrosGenericos ::: ")
        self.tokenGiro = GiroAuthenticate.traerTokenGiro(self)
        fechaHoy = self.hoy.strftime('%d/%m/%Y %H:%M:%S')

        idTipoOperacion = "11"
        operacion = "ObtenerRegistrosGenericos"
        operador = self.operador
        respuestas.GrabaRespuestas.limpiarDatos(self, self.operador, self.idLlamada, operacion, "ERROR")
        condicionesFiltro = [
            "FECUPD > CONVERT(DATETIME, '" + fechaHoy + "', 103)",
            "AND PLANTA = '" + self.codigPlantaAfip + "' ORDER BY FECUPD ASC"
        ]
        params = {
            'token': self.tokenGiro,
            'entidad': "IDSINTSMART",
            'condicionesFiltro': condicionesFiltro
        }

        self.clientFarm.transport.http_post = True  # Para usar POST
        self.clientFarm.transport.http_get = False  # Para desactivar GET
        respRegGen = self.clientFarm.service.ObtenerRegistrosGenerico(**params)
        if respRegGen['CodigoError'] == 0 and respRegGen['ResultXML'] == None:
            msg = "ObtenerRegistrosGenericos :: no hay registros para procesar."
            respuestas.GrabaRespuestas().grabarRespuesta(str(respRegGen['CodigoError']), msg, 0, 0, idTipoOperacion,
                                                        operacion, self.operador, "N", self.idLlamada, "",
                                                        "ERROR")

            print(msg)
        elif respRegGen['CodigoError'] == 0 and respRegGen['ResultXML'] != None:
            msg = ":: ObtenerRegistrosGenericos :: tiene registros para procesar"
            print(msg)
            #sample_array es la repuesta de giro con los registros genericos para procesar
            sample_array = [1, 2, 3]
            for i in range(0, len(sample_array)):
                idCampanaSmart = sample_array[i]
                resp = self.obtenerMlogis(idCampanaSmart)
                print("IDCAMPANASMART: " + str(idCampanaSmart) + " :: " + str(resp))
        elif respRegGen['CodigoError'] > 0 and respRegGen['ResultXML'] != None:
            err = errores.GrabaErrores()
            codigoError =respRegGen['CodigoError']
            descripcionError = respRegGen['ResultXML']
            err.grabarError(codigoError, descripcionError, 0, 0, self.hoy, idTipoOperacion, operacion, operador, 'N', self.codigPlantaAfip, self.idLlamada)
            return False






    def obtenerMlogis(self, idCampanaSmart):
        self.tokenGiro = GiroAuthenticate.traerTokenGiro(self)
        fechaHoy = self.hoy.strftime('%Y-%m-%d %H:%M:%S')
        idTipoOperacion = "12"
        operacion = "ObtenerMlogis"
        operador = self.operador
        params = {
            'Token': self.tokenGiro,
            'id': idCampanaSmart,

        }

        mLogisDatos = []
        self.clientFarm.transport.http_post = True  # Para usar POST
        self.clientFarm.transport.http_get = False  # Para desactivar GET
        respMlogis = self.clientFarm.service.ObtenerMlogis(**params)

        if respMlogis['CodigoError'] == 0 :
            # si la cantidad de registros es mayor a 0 tiene registros sino no tiene registros en posicion
            mLogisDatos.append(respMlogis['ResultXML'])
            perist = self.persistirMLogis(mLogisDatos, idTipoOperacion, operacion)
            if perist:
                msg = ":: ObtenerMlogis :: Registros procesados correctamente"
                return msg
            else:
                msg = ":: ObtenerMlogis :: Error al procesar los registros"
                return msg
        else:
            msg = ":: ObtenerMlogis :: No hay registros que procesar"
            return msg




    def persistirMLogis(self, datosMLogis, operacionCodigo, operacionNombre):
        '''
        se debe recorrer los dastos de MLogis que es el registro que tengo que grabar o actualizar
        '''
        if datosMLogis != None:
            cursor = self.conn.cursor()
            try:
                sql = (
                    "INSERT INTO DBA.giro_mlogis (id_giro, estadoLog, bruto, campana, codigoEstabDest, codigoEstabProc, fecha, "
                    "kgsBruto, kgsCarga, kgsDescarga, kgsEstimados, kgsTara, mSolicitud, nroComprobante, nroCupo, observacion, siloDesc, "
                    "stockId, stProceso, tara, tipoComprobante, tipoMov, totMerm, totNeto, zacco, variedad, recordGuid, userId, feccre, fecupd, cdc, origen, planta) "
                    "VALUES ( 'G12345', 'Active', 1000.00, '2023', 'A', 'P123', '2023-10-01 12:00:00', 1000.00, "
                    "950.00, 900.00, 920.00, 50.00, 'S123', 'C12345', 'CUP123', 'No observations', 'SILO1', 'STK123', "
                    "'Processed', 20.00, '1', '0',  10.00, 900.00, 'Z123', 'Variety1', 'GUID123', 12345, "
                    "'2023-10-01 12:00:00', '2023-10-01 12:00:00', 'CDC123', '0', '"+str(self.codigPlantaAfip)+"')")
                cursor.execute(sql)
                cursor.commit()
                return True
            except Exception as e:
                print(f"Error al ejecutar la consulta: {e}")
                cursor.execute("INSERT INTO giro_errores_ws (errorCodigo, errorDescripcion, nroTicket, nroCarta, fechaHora, idOperacion, operacion, operador, borradoLogico, entradaSalida, control, planta) "
                                "VALUES ('" + str(operacionCodigo) + "', '" + str(operacionNombre) + "', 0, 0, '" + str(self.hoy) + "', '" + str(0) + "', '" + str(0) + "', '" + str(self.operador) + "', 1, 'N', 'N', '" + str(self.codigoPlanta) + "')")
                cursor.commit()
                return False







    def _create_soap_client_farm(self):

        cursor = self.conn.cursor()
        sql = "SELECT valor from giro_parametros where grupo = 'farm' and nombreParametro in ('url_farm')"
        cursor.execute(sql)
        item = cursor.fetchall()
        for urlFarm in item[0]:
            url = urlFarm
            print(":: urlFarm: ---------> "+url)
        session = Session()
        session.verify = False  # Disable SSL certificate verification
        transport = Transport(session=session)
        return zeep.Client(wsdl=url, transport=transport)














    def main(self, operador, idLlamada=0):
        self.operador = str(operador)
        self.idLlamada = idLlamada


        print(":: VALIDANDO TOKEN DE ACCESO :: ")
        cursor = self.conn.cursor()
        cursor.execute("SELECT valor FROM giro_parametros where grupo = 'coope' and nombreParametro "
                       "in ('token_hash_id', 'planta_codigo', 'planta_codigo_afip', 'cliente')")
        rows = cursor.fetchall()

        conf = []
        if rows == None:
            print(
                ":::: Error: Código de cliente inválido.")
        else:
            if len(rows) > 0:
                for item in rows:
                    conf.append(item[0])
                self.codigoPlanta = conf[0]
                self.codigPlantaAfip = conf[2]

                token = conf[1]
                cli = conf[3]
                cli = ""

            if token == self.token:
                # verifico si esta autenticado y sino creo un nuevo token

                giroAuth = GiroAuthenticate()
                for giro in giroAuth.resp:
                    tokenGiro = giro.get("userToken")
                    respLoginGiroSucceeded = giro.get("LoginSucceeded")
                    respLoginGiroResultCode = giro.get("resultCode")
                    respLoginTokenMode = giro.get("status")

                    if respLoginGiroSucceeded == 'true' and respLoginGiroResultCode == "600":
                       print(":: TOKEN GIRO ES VALIDO: "+tokenGiro+" :: "+str(respLoginTokenMode)+" ::")
                       self.obtenerRegistrosGenericos()
                       # self.persistirChasisEnGiro(self.datosParaGiro, cli, tokenGiro )

                       print(":: TODOS LOS PROCESOS FUERON COMPLETADOS ::")

                    else:
                        # Usuario o clave de giros incorrectos
                         print(":: ERROR :: TOKEN DE ACCESO INVÁLIDO. (consulte con el administrador del sistema)")



                #print(":: TODOS LOS PROCESOS FUERON COMPLETADOS ::")

                self.conn.close()
            else:
                print(":: ERROR :: TOKEN DE ACCESO INVÁLIDO. (consulte con el administrador del sistema)")


if __name__ == "__main__":
    giros_reg = GirosObtenerRegistros()
    giros_reg.main("DBA", 23476226)

