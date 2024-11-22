# The common XML.RPC endpoint
import smtplib
from datetime import datetime, date
from email.message import EmailMessage
import zeep
from requests import Session
from zeep.transports import Transport
from conn.DBConnection import DBConnection as DBConnection
from giros_authenticate import GiroAuthenticate as GiroAuthenticate

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GiroTransporteChasis(DBConnection):
    def __init__(self):
        super().__init__()
        self.tokenGiro = ""
        self.config = []
        self.resp = []
        self.clientFarm = self._create_soap_client_farm()
        self.hoy = datetime.now()
        self.maskCuenta = "0000000"
        self.datos = []
        self.datosParaGiro = []

    def tomarDatosChasisSybase(self):

        print(":: MODULO TRANSPORTE CHASIS :: Aguarde un momento por favor ...")
        global datos
        cursor = self.conn.cursor()
        cursor.execute( "select tte_codigo, camion_codigo,chasis_patente, chasis_provincia, acoplado_patente, acoplado_provincia,chofer,tipo_doc, cuit, seguro, seg_chasis_vto from v_giro_transportes")
        items = cursor.fetchall()

        if len(items) > 0:
            for item in items:
                camion = item.camion_codigo
                chasisPatente = item.chasis_patente
                chasisProvincia = item.chasis_provincia,
                chofer = item.chofer
                tipoDocumento = item.tipo_doc
                cuit = item.cuit

                #Ver de donde se saca la tara que hay que informar porque es un dato que no tenemos
                tara = 1
                #
                seguroPoliza = item.seguro
                seguroPolizaVence = item.seg_chasis_vto
                vencCCar = ""
                detalle =""
                dnt = ""
                self.datosParaGiro.append([chasisPatente, seguroPoliza, tara, vencCCar, seguroPolizaVence, detalle, dnt])

            print(":: MODULO TRANSPORTE CHASIS :: PREPARADOS PARA ENVIAR A GIRO ::")
            self.persistirEnGiro(self.datosParaGiro)
           # EJECUTO CLASE clases/padronGiro que implementa el web service con giro y le informa el padronIngreso

        else:
            print("La busqueda no arrojo resultados")
            #return self.datosParaGiro






    def _create_soap_client_farm(self):

        cursor = self.conn.cursor()
        sql = "SELECT valor from giro_parametros where grupo = 'farm' and nombreParametro in ('url_farm_chasis')"
        cursor.execute(sql)
        item = cursor.fetchall()
        for urlFarm in item[0]:
            url = urlFarm
            print(":: urlFarm: ---------> "+url)
        session = Session()
        session.verify = False  # Disable SSL certificate verification
        transport = Transport(session=session)
        return zeep.Client(wsdl=url, transport=transport)




    def persistirEnGiro(self, datosParaGiro):
        # Borro todolo que no tenga ID ASIGNADO DE GIRO
        cursor = self.conn.cursor()
        #cursor.execute("delete from giro_chasis where id_giro = ''")>
        for chasisPatente, seguroPoliza, tara, vencCCar, seguroPolizaVence, detalle, dnt in datosParaGiro:
           
            if not chasisPatente:
                chasisPatente = "0"
            if not seguroPoliza:
                seguroPoliza = "0"
            if not tara:
                tara = 0.0
            if not vencCCar:
                vencCCar = datetime.now().isoformat()

            if not seguroPolizaVence:
                seguroPolizaVence = datetime.now().isoformat()


            if not detalle:
                detalle = "0"
            if not dnt:
                dnt = "0"




            params = {
                    'token': self.tokenGiro,
                    'chasis': {
                        'Patente': chasisPatente,
                        'Seguro': seguroPoliza,
                        'Tara': tara,
                        'VencCar': vencCCar,
                        'VencSeg': seguroPolizaVence,
                        'Detalle': detalle,
                        'DNT': dnt
                    }
                }


            self.clientFarm.transport.http_post = True  # Para usar POST
            self.clientFarm.transport.http_get = False  # Para desactivar GET
            try:
                respChasis = self.clientFarm.service.MChasisCreate(**params)
                if respChasis.CodigoError == 0:

                    if  respChasis.Result is None:
                        idGiro = "no-devuelve-id"
                    else:
                        idGiro = respChasis.Result
                    if isinstance(vencCCar, str):
                        vencCCar = datetime.fromisoformat(vencCCar)
                    if isinstance(seguroPolizaVence, str):
                        seguroPolizaVence = datetime.fromisoformat(seguroPolizaVence)

                    # Convert to date only if they are datetime objects
                    if isinstance(vencCCar, datetime):
                        vencCCar = vencCCar.date()
                    if isinstance(seguroPolizaVence, datetime):
                        seguroPolizaVence = seguroPolizaVence.date()
                    cursor.execute("SELECT COUNT(*) FROM giro_chasis WHERE patente = ? ", (chasisPatente,))
                    record_exists = cursor.fetchone()[0]
                    if record_exists == 0:
                        # Record does not exist, proceed with insertion
                        sql = (
                            "INSERT INTO giro_chasis (id_giro, patente, seguro, tara, vencCar, vencSeg, detalle, dnt, informado_sn) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'S')")
                        cursor.execute(sql, (
                        idGiro, chasisPatente, seguroPoliza, tara, str(vencCCar), str(seguroPolizaVence), detalle, dnt))
                        self.conn.commit()
                    else:
                        sql = (
                            "UPDATE giro_chasis SET id_giro = ?, seguro = ?, tara = ?, vencCar = ?, vencSeg = ?, detalle = ?, dnt = ?, informado_sn = 'S' "
                            "WHERE patente = ?")
                        cursor.execute(sql, (
                            idGiro, seguroPoliza, tara, str(vencCCar), str(seguroPolizaVence), detalle, dnt,
                            chasisPatente))
                        self.conn.commit()
                    print(":: Modulo Transporte Chasis, patente " + str(chasisPatente) + " se informo/actualizo con éxito:: ")





                else:
                    print(
                        f"Error en la respuesta del servicio: {getattr(respChasis, 'MensajeError', 'MensajeError no encontrado')}")
            except zeep.exceptions.Fault as fault:
                print(f"SOAP Fault: {fault}")
                return False
            except Exception as e:
                print(f"Unexpected error: {e}")
                return False









    def consultarChasisEnGiro(self, chasisPatente):
        params = {
            'token': self.tokenGiro,
            'id': "b32e590-0a4a-4133-a6dc-415b2a8"
        }
        data=[]

        self.clientFarm.transport.http_post = True  # Para usar POST
        self.clientFarm.transport.http_get = False  # Para desactivar GET
        try:
            respChasis = self.clientFarm.service.MChasisReadByID(**params)

            if respChasis.CodigoError == 0:

              if respChasis["Result"] is not None:
                data.append(respChasis["Result"])
                #select codigo, respuesta, nroTicket, nroCarta, fechaHora, idOperacion, operacion, operador, borradoLogico, entradaSalida, idLlamada, descripcion, tipo from  giro_respuesta_ws
                print(f":: Chasis {chasisPatente} :: La información se recuperó con éxito.")
                print(":: Chasis {chasisPatente} :: "+str(data[0]))
                print(data[0]["Patente"]+" "+str(data[0]["Seguro"])+" "+str(data[0]["Tara"])+" "+str(data[0]["VencCar"])+" "+str(data[0]["VencSeg"])+" "+data[0]["Detalle"]+" "+str(data[0]["DNT"]))

              else:
                  print(f":: Chasis {chasisPatente} :: La busqueda no arrojo ningún resultado.")








            else:
               print(f"Error en la respuesta del servicio: {getattr(respChasis, 'MensajeError', 'MensajeError no encontrado')}")
        except zeep.exceptions.Fault as fault:
                print(f"SOAP Fault: {fault}")
                return False
        except Exception as e:
                print(f"Unexpected error: {e}")
                return False






    def main(self):
        #import conn.sybase
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

                plantaCodigo = conf[0]
                token = conf[1]
                plantaCodigoAfip = conf[2]
                cli = conf[3]
                cli = ""

            if token == self.token:
                print(":: TOKEN LOCAL AUTORIZADO :: ")
                # verifico si esta autenticado y sino creo un nuevo token

                giroAuth = GiroAuthenticate()
                for giro in giroAuth.resp:
                    tokenGiro = giro.get("userToken")
                    respLoginGiroSucceeded = giro.get("LoginSucceeded")
                    respLoginGiroResultCode = giro.get("resultCode")
                    respLoginTokenMode = giro.get("status")
                    if respLoginGiroSucceeded == 'true' and respLoginGiroResultCode == "600":
                        print(":: TOKEN GIRO ES VALIDO: "+tokenGiro+" :: "+str(respLoginTokenMode)+" ::")
                        self.tokenGiro = GiroAuthenticate.traerTokenGiro(self)
                        #self.consultarChasisEnGiro("AE513HE")
                        self.tomarDatosChasisSybase()

                    else:
                        # Usuario o clave de giros incorrectos
                        return False



                #print(":: TODOS LOS PROCESOS FUERON COMPLETADOS ::")

                self.conn.close()
            else:
                print(":: ERROR :: TOKEN DE ACCESO INVÁLIDO. (consulte con el administrador del sistema)")


if __name__ == "__main__":
    giros_transporte_chasis = GiroTransporteChasis()
    giros_transporte_chasis.main()

