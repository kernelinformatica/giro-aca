# The common XML.RPC endpoint
import smtplib
from datetime import datetime, date
from email.message import EmailMessage

import zeep
from requests import Session
from zeep.transports import Transport
from conn.DBConnection import DBConnection as DBConnection
from giros_authenticate import GiroAuthenticate as GiroAuthenticate





class GiroProvincias(DBConnection):
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

    def tomarDatosSybase(self):

        print(":: MODULO PROVINCIAS  :: Aguarde un momento por favor ...")
        global datos
        cursor = self.conn.cursor()
        cursor.execute( "SELECT codigo_provi, provi_descri, provi_resol, pais FROM ctacte_provincia")
        items = cursor.fetchall()
        if len(items) > 0:
            for item in items:

                codigo = item.codigo_provi
                nombre = item.provi_descri
                pais = "ARGENTINA"
                self.datosParaGiro.append([codigo, nombre, pais])

            self.persistirEnGiro(self.datosParaGiro)

        else:
            print("La busqueda no arrojo resultados")
            #return self.datosParaGiro






    def _create_soap_client_farm(self):

        cursor = self.conn.cursor()
        sql = "SELECT valor from giro_parametros where grupo = 'farm' and nombreParametro in ('url_farm_provincias')"
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


        for codigo, nombre, pais in datosParaGiro:



            params = {
                    'token': self.tokenGiro,
                    'provincia': {
                        'Nombre': nombre,
                        'Pais': pais,
                    }
                }
            i=i+1

            self.clientFarm.transport.http_post = True  # Para usar POST
            self.clientFarm.transport.http_get = False  # Para desactivar GET
            try:


                cursor.execute("SELECT COUNT(*) FROM giro_provincias WHERE nombre = ? ", (nombre,))
                record_exists = cursor.fetchone()[0]

                resp = self.clientFarm.service.MProvinciaCreate(**params)
                '''                if record_exists == 0:


                    if resp.Result is None:
                        idGiro = "no-devuelve-id"
                    else:
                        idGiro = resp.Result
                    # Record does not exist, proceed with insertion
                    sql = (
                        "INSERT INTO giro_provincias (id_giro,  codigo, nombre, pais) "
                        "VALUES (?, ?, ?, ?)")
                    cursor.execute(sql, (idGiro, codigo, nombre, pais))
                    self.conn.commit()
                    print(":: Modulo Provincias  " + str(nombre) + ": " + str(
                        nombre) + " se informo con éxito:: ")


                if resp.CodigoError == 0:

                   print(f":: Provincia {nombre} :: La información se guardó con éxito. ID: {codigo}")


                elif resp.CodigoError == 500:

                    #si existe ya registrado tira aca
                    print(":: "+str(nombre)+", "+str(codigo)+ ", ya se encuentra registrado en giro.")'''

            except zeep.exceptions.Fault as fault:
                print(f"SOAP Fault: {fault}")
                #return False
            except Exception as e:
                print(f"Unexpected error: {e}")
                #return False















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
                        self.tomarDatosSybase()

                    else:
                        # Usuario o clave de giros incorrectos
                        return False



                #print(":: TODOS LOS PROCESOS FUERON COMPLETADOS ::")

                self.conn.close()
            else:
                print(":: ERROR :: TOKEN DE ACCESO INVÁLIDO. (consulte con el administrador del sistema)")


if __name__ == "__main__":
    giro_pronvincias = GiroProvincias()
    giro_pronvincias.main()

