# The common XML.RPC endpoint
import smtplib
from datetime import datetime, date
from email.message import EmailMessage

import zeep
from requests import Session
from zeep.transports import Transport
from conn.DBConnection import DBConnection as DBConnection
from giros_authenticate import GiroAuthenticate as GiroAuthenticate





class GiroTransporteChoferes(DBConnection):
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

    def tomarDatosChoferesSybase(self):

        print(":: MODULO TRANSPORTE ACOPLADO :: Aguarde un momento por favor ...")
        global datos
        cursor = self.conn.cursor()
        cursor.execute( "select chofer, cuit from v_giro_transportes where tte_codigo between 1 and 7")
        items = cursor.fetchall()
        if len(items) > 0:
            for item in items:

                chofer = item.chofer
                cuit = item.cuit
                sql ="select  padron_ivacon, ctacte_padron.codigo_postal, padron_domici+' '+padron_domnro as domicilio, ctacte_localidad.codigo_provi as provincia from ctacte_padron, ctacte_localidad where (padron_cuit11 = "+str(cuit)+" or padron_cuil11 = "+str(cuit)+") and ctacte_padron.codigo_postal = ctacte_localidad.codigo_postal"
                cursor.execute(sql)
                print()
                it = cursor.fetchall()
                if len(it) > 0:
                    for ite in it:

                        ivaCondicion = ite.padron_ivacon
                        codigoPostal = ite.codigo_postal
                        domicilio = ite.domicilio
                        codigoProvincia =ite.provincia

                self.datosParaGiro.append([cuit, chofer, ivaCondicion, codigoProvincia, codigoPostal, domicilio])


            self.persistirEnGiro(self.datosParaGiro)
           # EJECUTO CLASE clases/padronGiro que implementa el web service con giro y le informa el padronIngreso

        else:
            print("La busqueda no arrojo resultados")
            #return self.datosParaGiro






    def _create_soap_client_farm(self):

        cursor = self.conn.cursor()
        sql = "SELECT valor from giro_parametros where grupo = 'farm' and nombreParametro in ('url_farm_choferes')"
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
        i =0

        #cursor.execute("delete from giro_chasis where id_giro = ''")>
        for cuit, chofer, ivaCondicion, codigoProvincia, codigoPostal, domicilio in datosParaGiro:



            params = {
                    'token': self.tokenGiro,
                    'chofer': {
                        'CUIT': cuit,
                        'Nombre': chofer,
                        'CodPostal': codigoPostal,
                        'CondIva': ivaCondicion,
                        'Cuenta': 0,
                        'Domicilio': domicilio,
                        'Orden': i,
                        'Provincia': codigoProvincia
                    }
                }
            i=i+1

            self.clientFarm.transport.http_post = True  # Para usar POST
            self.clientFarm.transport.http_get = False  # Para desactivar GET
            try:


                cursor.execute("SELECT COUNT(*) FROM giro_choferes WHERE cuit = ? ", (cuit,))
                record_exists = cursor.fetchone()[0]


                if record_exists == 0:
                    resp = self.clientFarm.service.MChoferCreate(**params)
                    if resp.Result is None:
                        idGiro = "no-devuelve-id"
                    else:
                        idGiro = resp.Result
                    # Record does not exist, proceed with insertion
                    sql = (
                        "INSERT INTO giro_choferes (id_giro, nombre, codPostal, condIva, cuenta, domicilio, orden, provincia, cuit) "
                        "VALUES (?, ?, ?, ?, ?, ?,  ?, ?,?)")
                    cursor.execute(sql, (idGiro, chofer, codigoPostal, ivaCondicion, 0, domicilio, i, codigoProvincia, cuit))
                    self.conn.commit()
                    print(":: Modulo Transporte choferes, cuit " + str(cuit) + ": " + str(
                        chofer) + " se informo con éxito:: ")
                else:
                    resp = self.clientFarm.service.MChoferUpdate(**params)
                    if resp.Result is None:
                        idGiro = "no-devuelve-id"
                    else:
                        idGiro = resp.Result
                    #aca tengo que ver como actualizar en giro, si borrar el registro y volverlo a pasar o como hacer un update
                    sql = ("UPDATE giro_choferes SET id_giro = ?, nombre = ?, codPostal = ?,  condIva = ?, cuenta = ?, domicilio = ?, orden = ?, provincia = ? "
                        "WHERE cuit = ?")
                    cursor.execute(sql, (idGiro, chofer, codigoPostal, ivaCondicion, 0, domicilio, i, codigoProvincia, cuit))
                    self.conn.commit()
                print(":: Modulo Transporte choferes, cuit " + str(cuit) + ": " + str(
                    chofer) + " se actualizo con éxito:: ")


                if resp.CodigoError == 0:

                   print(f":: Chofer {cuit} :: La información se guardó con éxito. ID: {idGiro}")


                elif resp.CodigoError == 500:
                    #si existe ya registrado tira aca
                    for error in resp.Errors.CodeError:
                        code = error['Code']
                        message = error['Message']
                    print("Error en la respuesta del servicio "+str(cuit)+", "+str(chofer)+": "+str(code)+": "+str(message))

            except zeep.exceptions.Fault as fault:
                print(f"SOAP Fault: {fault}")
                #return False
            except Exception as e:
                print(f"Unexpected error: {e}")
                #return False









    def consultarEnGiro(self, nroDocumentoCuit):
        params = {
            'token': self.tokenGiro,
            'id': "b32e590-0a4a-4133-a6dc-415b2a8"
        }
        data=[]

        self.clientFarm.transport.http_post = True  # Para usar POST
        self.clientFarm.transport.http_get = False  # Para desactivar GET
        try:
            resp = self.clientFarm.service.MChoferReadByID(**params)

            if resp.CodigoError == 0:

              if resp["Result"] is not None:
                data.append(resp["Result"])
                #select codigo, respuesta, nroTicket, nroCarta, fechaHora, idOperacion, operacion, operador, borradoLogico, entradaSalida, idLlamada, descripcion, tipo from  giro_respuesta_ws
                print(f":: Chofer {nroDocumentoCuit} :: La información se recuperó con éxito.")
                print(f":: Chofer {nroDocumentoCuit}:: "+str(data[0]))
               # print(data[0]["Patente"]+" "+str(data[0]["Seguro"])+" "+str(data[0]["Tara"])+" "+str(data[0]["VencCar"])+" "+str(data[0]["VencSeg"])+" "+data[0]["Detalle"]+" "+str(data[0]["DNT"]))

              else:
                  print(f":: Chasis {resp} :: La busqueda no arrojo ningún resultado.")








            else:
               print(f"Error en la respuesta del servicio: {getattr(resp, 'MensajeError', 'MensajeError no encontrado')}")
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
                        self.tomarDatosChoferesSybase()

                    else:
                        # Usuario o clave de giros incorrectos
                        return False



                #print(":: TODOS LOS PROCESOS FUERON COMPLETADOS ::")

                self.conn.close()
            else:
                print(":: ERROR :: TOKEN DE ACCESO INVÁLIDO. (consulte con el administrador del sistema)")


if __name__ == "__main__":
    giros_transporte_choferes = GiroTransporteChoferes()
    giros_transporte_choferes.main()

