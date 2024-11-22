# The common XML.RPC endpoint
import smtplib
from datetime import datetime, date
from email.message import EmailMessage
import respuestas
import zeep
from requests import Session
from zeep.transports import Transport
from conn.DBConnection import DBConnection as DBConnection
from giros_authenticate import GiroAuthenticate as GiroAuthenticate





class GiroLocalidades(DBConnection):
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
        cursor.execute( "SELECT codigo_postal, localidad_nombre,nro_onnca, codigo_provincia, nombre_departamento, codigo_dep_afip, id_provincia_giro,id_localidad FROM v_giro_localidades")
        items = cursor.fetchall()
        if len(items) > 0:
            for item in items:
                id_localidad = item.id_localidad
                codigo = item.codigo_postal
                nombre = item.localidad_nombre
                loc_nro_onnca = item.nro_onnca
                provincia = item.codigo_provincia
                nombre_departamento = item.nombre_departamento
                codigo_dep_afip = item.codigo_dep_afip
                id_provincia_giro = item.id_provincia_giro

                self.datosParaGiro.append([codigo, nombre, loc_nro_onnca, provincia, nombre_departamento, codigo_dep_afip, id_provincia_giro, id_localidad])

            self.persistirEnGiro(self.datosParaGiro)

        else:
            print("La busqueda no arrojo resultados")
            #return self.datosParaGiro






    def _create_soap_client_farm(self):

        cursor = self.conn.cursor()
        sql = "SELECT valor from giro_parametros where grupo = 'farm' and nombreParametro in ('url_farm_localidades')"
        cursor.execute(sql)
        item = cursor.fetchall()
        for urlFarm in item[0]:
            url = urlFarm
            print(":: urlFarm: ---------> "+url)
        session = Session()
        session.verify = False  # Disable SSL certificate verification
        transport = Transport(session=session)
        return zeep.Client(wsdl=url, transport=transport)


    def eliminarLocalidad(self, operador, idLlamada=0, idLocalidad=""):
        idTipoOperacion = 16
        operacion = "MLocalidadRemove"
        if idLocalidad > 0 or idLocalidad != "":
            self.clientFarm.transport.http_post = True
            self.clientFarm.transport.http_post = True  # Para usar POST
            self.clientFarm.transport.http_get = False  # Para desactivar GET
            cursor = self.conn.cursor()
            try:

                cursor.execute("SELECT COUNT(*) FROM giro_localidades WHERE id_giro = ? ", (idLocalidad,))
                record_exists = cursor.fetchone()[0]
                i = 0

                if record_exists > 0:

                    try:
                        params = {
                            'token': self.tokenGiro,
                            'localidad': {
                                'LocalidadID': idLocalidad,

                            }
                        }
                        i = i + 1
                        resp = self.clientFarm.service.MLocalidadCreate(**params)
                        if resp.CodigoError == 0:
                            sql = ("DELETE FROM giro_localidades WHERE id_giro = ?", (idLocalidad,))
                            cursor.execute(sql)
                            self.conn.commit()
                            print(":: Modulo Localidades :: Eliminar localidad: " + str(idLocalidad) + ", se elimino con éxito:: ")
                        elif resp.CodigoError == 500:
                            for error in resp.Errors['CodeError']:
                                print(":: Localidades Error (" + str(resp.CodigoError) + "): " + str(
                                    idLocalidad) + ": " + error.Message)
                        elif resp.CodigoError == 401:
                            for error in resp.Errors['CodeError']:
                                print(":: Localidades Error (" + str(resp.CodigoError) + "): " + str(
                                    idLocalidad) + ": " + error.Message)



                    except zeep.exceptions.Fault as fault:
                        print(f"SOAP Fault: {fault}")
                    except Exception as e:
                        print(f"Unexpected error: {e}")

                elif record_exists == 0:
                    idTipoOperacion = 17
                    operacion = "MLocalidadRemove"
                    tipo = "OK"
                    msg = ":: Eliminar Localidades: " + str(idLocalidad) + " (" + str(operador) + ")"
                    respuestas.GrabaRespuestas().grabarRespuesta(401, msg, 0, 0, idTipoOperacion, operacion, operador, "N",
                                                                 idLlamada, "Metodo no implementado porque no existe", tipo)
                    print(msg)
            except Exception as e:
                print(f":: Ocurrió un error inesperado, intentar borrar la localidad en giro: {e}")
                #

        else:
            msg= ":: Error: Tipo operacion: "+str(idTipoOperacion)+": "+str(operacion)+"No se recibió el ID de la localidad a eliminar."
            print(msg)
            return msg


    def persistirEnGiro(self, datosParaGiro):
        # Borro todolo que no tenga ID ASIGNADO DE GIRO
        cursor = self.conn.cursor()
        i =0
        idTipoOperacion = 13
        operacion = "MLocalidadCreate"
        respuestas.GrabaRespuestas.limpiarDatos(self, self.operador, self.idLlamada, operacion, "ERROR")
        respuestas.GrabaRespuestas.limpiarDatos(self, self.operador, self.idLlamada, "MLocalidadUpdate", "ERROR")
        respuestas.GrabaRespuestas.limpiarDatos(self, self.operador, self.idLlamada, operacion, "OK")


        for codigo, nombre, loc_nro_onnca, provincia, nombre_departamento, codigo_dep_afip, id_provincia_giro, id_localidad in datosParaGiro:



            params = {
                    'token': self.tokenGiro,
                    'localidad': {
                        'NOMBRE': nombre,
                        'LOCRG3789': loc_nro_onnca,
                        'DPTRG3789': codigo_dep_afip,
                        'PRORG3789': provincia,
                        'PROVINCIAID': id_provincia_giro,
                    }
                }
            i=i+1

            self.clientFarm.transport.http_post = True  # Para usar POST
            self.clientFarm.transport.http_get = False  # Para desactivar GET
            try:


                cursor.execute("SELECT COUNT(*) FROM giro_localidades WHERE codigo_loc_afip = ? ", (loc_nro_onnca,))
                record_exists = cursor.fetchone()[0]


                if record_exists == 0:

                    try:
                        resp = self.clientFarm.service.MLocalidadCreate(**params)
                        if resp.CodigoError == 0:
                            # si alguna vez giro me devuelve el id del registro creado, lo guardo en la base de datos y se lo asigno a la variable idGiro
                            idGiro = None
                            if idGiro is None :
                                idGiro = "no-devuelve-id-de-retorno"
                            else:
                                idGiro = resp.Result
                            sql = ("INSERT INTO giro_localidades (id_giro,  nombre, codigo_loc_afip, provincia_id, id_prov_giro, codigo_dep_afip, codigo_prov_afip) "
                                "VALUES (?, ?, ?, ?, ?, ?,?)")
                            cursor.execute(sql, ( idGiro, nombre, loc_nro_onnca, provincia, id_provincia_giro, codigo_dep_afip,
                                           provincia))
                            self.conn.commit()
                            print(":: Modulo Provincias  " + str(nombre) + ": " + str(
                                nombre) + " se informo con éxito:: ")
                        elif resp.CodigoError == 500:
                            for error in resp.Errors['CodeError']:
                                idGiro = None
                                if idGiro is None:
                                    idGiro = "no-devuelve-id-de-retorno"
                                else:
                                    idGiro = resp.Result
                                sql = (
                                    "INSERT INTO giro_localidades (id_giro,  nombre, codigo_loc_afip, provincia_id, id_prov_giro, codigo_dep_afip, codigo_prov_afip) "
                                    "VALUES (?, ?, ?, ?, ?, ?,?)")
                                cursor.execute(sql, (
                                idGiro, nombre, loc_nro_onnca, provincia, id_provincia_giro, codigo_dep_afip,
                                provincia))
                                self.conn.commit()
                                print(":: Localidades Error ("+str(resp.CodigoError)+"): " + str(loc_nro_onnca) + ": " + str(nombre) + " (" + str(
                                    provincia) + "): " + error.Message)
                        elif resp.CodigoError == 401:
                            for error in resp.Errors['CodeError']:
                                print(":: Localidades Error ("+str(resp.CodigoError)+"): "+str(loc_nro_onnca)+": "+str(nombre)+" ("+str(provincia)+"): "+error.Message)





                    except zeep.exceptions.Fault as fault:
                        print(f"SOAP Fault: {fault}")
                    #except Exception as e:
                        #print(f"Unexpected error: {e}")


                elif record_exists > 0:
                    idTipoOperacion = 14
                    operacion = "MLocalidadUpdate"
                    tipo = "ERROR"
                    msg=":: Localidad ya registrada en GIRO, método "+str(operacion)+" con Giro sin inplementar: " + str(loc_nro_onnca) + ": " + str(nombre) + " (" + str(provincia) + ")"
                    print(msg)
                    respuestas.GrabaRespuestas().grabarRespuesta(401, msg, 0, 0, idTipoOperacion, operacion, self.operador, "N", self.idLlamada, "Metodo no implementado porque no existe", tipo)
                    """
                     try:
                        resp = self.clientFarm.service.MLocalidadUpdate(**params)
                        if resp.CodigoError == 0:

                            if resp.Result is None:
                                idGiro = "no-devuelve-id"
                            else:
                                idGiro = resp.Result
                            sql = (
                                "UPDATE giro_localidades SET "
                                "nombre = ?, "
                                "codigo_loc_afip = ?, "
                                "provincia_id = ?, "
                                "id_prov_giro = ?, "
                                "codigo_dep_afip = ?, "
                                "codigo_prov_afip = ? "
                                "WHERE id_giro = ?"
                            )
                            cursor.execute(sql, (nombre, loc_nro_onnca, provincia, id_provincia_giro, codigo_dep_afip, provincia, idGiro), id_localidad,)
                            self.conn.commit()
                            print(":: Modulo Provincias  " + str(nombre) + ": " + str(nombre) + " se actualizo con éxito:: ")
                        elif resp.CodigoError == 500:
                            for error in resp.Errors['CodeError']:
                                if resp.Result is None:
                                    idGiro = "no-devuelve-id"
                                else:
                                    idGiro = resp.Result
                                sql = (
                                    "INSERT INTO giro_localidades (id_giro,  nombre, codigo_loc_afip, provincia_id, id_prov_giro, codigo_dep_afip, codigo_prov_afip) "
                                    "VALUES (?, ?, ?, ?, ?, ?,?)")
                                cursor.execute(sql, (
                                idGiro, nombre, loc_nro_onnca, provincia, id_provincia_giro, codigo_dep_afip,
                                provincia))
                                self.conn.commit()
                                print(":: Localidades Error ("+str(resp.CodigoError)+"): " + str(loc_nro_onnca) + ": " + str(nombre) + " (" + str(
                                    provincia) + "): " + error.Message)
                        elif resp.CodigoError == 401:
                            for error in resp.Errors['CodeError']:
                                print(":: Localidades Error ("+str(resp.CodigoError)+"): "+str(loc_nro_onnca)+": "+str(nombre)+" ("+str(provincia)+"): "+error.Message)

                    



                    except zeep.exceptions.Fault as fault:
                        print(f"SOAP Fault: {fault}")
                    except Exception as e:
                        print(f"Unexpected error: {e}")
                    """

            except zeep.exceptions.Fault as fault:
                print(f"SOAP Fault: {fault}")
                #return False
            except Exception as e:
                print(f"Unexpected error: {e}")
                #return False















    def main(self, operador, idLlamada=0):
        self.operador = operador
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
    giro_localidades = GiroLocalidades()
    giro_localidades.main('DBA', 12345)

