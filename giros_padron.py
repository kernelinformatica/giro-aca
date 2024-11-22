# The common XML.RPC endpoint
import smtplib
from datetime import datetime
from email.message import EmailMessage
import ssl
print(ssl.OPENSSL_VERSION)
import zeep
from requests import Session
from zeep.transports import Transport
from conn.DBConnection import DBConnection as DBConnection
from giros_authenticate import GiroAuthenticate as GiroAuthenticate

import respuestas



class GirosPadron(DBConnection):
    def __init__(self):
        super().__init__()
        self.tokenGiro = ""
        self.config = []
        self.resp = []
        self.clientFarm = self._create_soap_client_farm()
        self.hoy = datetime.now()

        self.maskCuenta = "0000000"
        self.datosPadron = []
        self.datosPadronParaGiro = []

    def tomarDatosybase(self, codigo, plantaCodigo):

        print(":: MODULO PADRON :: Aguarde un momento por favor ...")
        global datos
        cursor = self.conn.cursor()
        if codigo == 0:
            cursor.execute(
                "SELECT  padron_codigo, padron_apelli, padron_nombre, padron_domici, padron_domnro, padron_domdto, "
                "padron_dompis, codigo_postal, padron_telcar, padron_telnro, padron_actanr, padron_ingres, "
                "codigo_docu, padron_docnro, padron_ivacon, desc_cond_iva, interes_tasa, padron_jncnro, padron_gananc, "
                "padron_apinro, padron_zonnro, padron_catego, catego_descri, padron_jubila, padron_cuit11, padron_cuil11, "
                "padron_busco1, padron_busco2, padron_observa, provincia, localidad, provincia_codigo, codigo_provincia_giro, tipo_cuenta_opera_como, id_localidad_afip FROM v_giro_ctacte_padron   order by padron_codigo asc")
        else:
            cursor.execute(
                "SELECT padron_codigo, padron_apelli, padron_nombre, padron_domici, padron_domnro, padron_domdto, "
                "padron_dompis, codigo_postal, padron_telcar, padron_telnro, padron_actanr, padron_ingres, "
                "codigo_docu, padron_docnro, padron_ivacon, desc_cond_iva,  interes_tasa, padron_jncnro, padron_gananc, "
                "padron_apinro, padron_zonnro, padron_catego, catego_descri, padron_jubila, padron_cuit11, padron_cuil11, "
                "padron_busco1, padron_busco2, padron_observa, provincia, localidad, provincia_codigo, codigo_provincia_giro, tipo_cuenta_opera_como, id_localidad_afip FROM v_giro_ctacte_padron where padron_codigo =  " + str(
                    codigo) + " order by padron asc")
        socios = cursor.fetchall()

        if len(socios) > 0:
            for a in socios:
                padronCodigo = a.padron_codigo
                padronNombreApellido = a.padron_apelli + " " + a.padron_nombre
                padronDomicilio = str(a.padron_domici) #+" "+str(a.padron_domnro)
                if isinstance(a.padron_domnro, str) == True:
                    padronDomicilioNro = 0
                else:
                    padronDomicilioNro = str(a.padron_domnro)
                padronCodigoPostal = a.codigo_postal
                padronProvinciaNombre = a.provincia
                codigoProvinciaGiro = a.codigo_provincia_giro
                padronProvinciaCodigo = a.provincia_codigo
                padronCategoria = a.padron_catego
                padronLocalidadNombre = a.localidad
                padronTelCar = a.padron_telcar
                padronTelNro = a.padron_telnro
                padronIngreso = a.padron_ingres
                padronNroDocumento = a.padron_docnro
                padronCondicionIva = a.padron_ivacon
                padronCondicionIvaNombre = a.desc_cond_iva
                padronJnrNro = a.padron_jncnro
                padronGanancias = a.padron_gananc
                padronApiNro = a.padron_apinro
                padronZonaNro = a.padron_zonnro
                padronCategoria = a.padron_catego
                padronCategoriaGiro = a.tipo_cuenta_opera_como
                padronCategoriaNombre = a.catego_descri
                padronJubilacion = a.padron_jubila
                idLocalidadAfip = a.id_localidad_afip
                if idLocalidadAfip == 0:
                    cursor.execute("SELECT nro_establecimiento FROM cereal_destinos where padron_codigo = "+str(a.padron_codigo)+" and codigo_postal ="+str(a.codigo_postal)+" ")
                    row = cursor.fetchone()
                    idLocalidadAfip = row[0]
                if  a.padron_cuit11 == None:
                    padronCuit = a.padron_cuil11
                else:
                    padronCuit = a.padron_cuit11
                padronObserva = a.padron_observa
                # padronTipoCuenta: Giro define este valor como INTERNA = 1 o EXTERNA = 2
                padronTipoCuenta = 1
                if idLocalidadAfip > 0:
                 self.datosPadronParaGiro.append(
                    [padronCodigo, padronNombreApellido, padronCondicionIva, padronCodigoPostal, padronCuit, padronDomicilio, padronDomicilioNro, padronLocalidadNombre, "ARGENTINA", padronProvinciaNombre, padronTipoCuenta, codigoProvinciaGiro, padronCategoria, padronCategoriaGiro, idLocalidadAfip])




        else:
            print("La busqueda no arrojo resultados")
        return self.datosPadron









    def persistirEnGiro(self, padronParaGiro):

        idTipoOperacion = 15
        operacion = "MaestroCuentasCreate"
        cursor = self.conn.cursor()
        p = 0
        respuestas.GrabaRespuestas.limpiarDatos(self, self.operador, self.idLlamada, operacion, "ERROR")
        respuestas.GrabaRespuestas.limpiarDatos(self, self.operador, self.idLlamada, "MaestroCuentasUpdate", "ERROR")

        for padronCodigo, padronNombreApellido, padronCondicionIva, padronCodigoPostal, padronCuit, padronDomicilio, padronDomicilioNro, padronLocalidadNombre, pais, padronProvinciaNombre, padronTipoCuenta, codigoProvinciaGiro, padronCategoria, padronCategoriaGiro, idLocalidadAfip  in padronParaGiro:
            localidad = cursor.execute("SELECT id_giro FROM giro_localidades where codigo_loc_afip = "+str(idLocalidadAfip)+"")
            rowLocalidad = localidad.fetchone()[0]
            if rowLocalidad is not None and rowLocalidad != 0:
                padronLocalidadId = rowLocalidad
            else:
                padronLocalidadId =0

            params = {
                'token':  self.tokenGiro,
                'cuenta': {
                    'Nombre': padronNombreApellido,
                    'CUIT': padronCuit,
                    'CondIVA': padronCondicionIva,
                    'CodPostal': padronCodigoPostal,
                    'Domicilio': padronDomicilio,
                    'Localidad': padronLocalidadNombre,
                    'Provincia': codigoProvinciaGiro,
                    'Pais': pais,
                    'TCINTERXTER': 1,
                    'CuentasHIjas': {
                        'CuentasHijaDTO': [
                            {
                                'IDRelacionInterfaz': padronCodigo,
                                'CUIT': padronCuit,
                                'Nombre': padronNombreApellido,
                                'IDDestinoGral': 0,
                                'Latitud': 0,
                                'Longitud': 0,
                                'CodPostal': padronCodigoPostal,
                                'CodAbrev': padronCodigoPostal,
                                'Domicilio': padronDomicilio,
                                'NroDomicilio': padronDomicilioNro,
                                'LocalidadID': str(padronLocalidadId),
                                'Provincia': codigoProvinciaGiro,
                                'Pais': pais,
                                'NroPlanta': 0,
                                'PTAONCCA': idLocalidadAfip,
                                'TipoCuenta': padronCategoriaGiro,
                                'TipoPlanta': ''
                            },

                        ]
                    }
                }
            }


            self.clientFarm.transport.http_post = True  # Para usar POST
            self.clientFarm.transport.http_get = False  # Para desactivar GET
            try:
                cursor.execute("SELECT COUNT(*) FROM giro_padron WHERE padron = " + str(padronCodigo))
                record_exists = cursor.fetchone()[0]
                # resp = 0
                resp = self.clientFarm.service.MaestroCuentasCreate(**params)
                err = ""
                if record_exists == 0:
                    # No existe el registro en la tabla giro_padron
                    if resp.CodigoError == 0:
                        idGiro = padronCodigo
                        sql = """
                        INSERT INTO "DBA"."giro_padron" (id_giro, padron, nombre, condicion_iva, padron_catego, padron_catego_giro, informado)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """
                        values = (idGiro, padronCodigo, padronNombreApellido, padronCondicionIva, padronCategoria,
                                  padronCategoriaGiro, 1)
                        cursor.execute(sql, values)
                        self.conn.commit()

                        msg = padronNombreApellido + ": " + str(padronCodigo)+" (Cuit: "+str(padronCuit)+") :: La cuenta se informó con éxito"
                        respuestas.GrabaRespuestas().grabarRespuesta("0", msg, 0, 0, idTipoOperacion, operacion,
                                                                     self.operador, "N", self.idLlamada, "", "OK")
                        print(":: MODULO PADRON " + str(msg) + " :: INFORMADO ::")

                    else:
                        ## VER ACA VER SUPUESTOS TRATAMIENTO DE ERRORES ETC
                        print(
                            ":: MODULO PADRON " + str(padronCodigo) + ": " + padronNombreApellido + " :: ACTUALIZA ::")
                else:
                    for err in resp.Errors['CodeError']:
                        msg = padronNombreApellido + ": " + str(padronCodigo) + " :: Error codigo: " + str(
                            err['Code']) + " - " + str(err['Message'].replace("'", '"'))
                        respuestas.GrabaRespuestas().grabarRespuesta(str(err['Code']), msg, 0, 0, idTipoOperacion,
                                                                     operacion, self.operador, "N", self.idLlamada, "",
                                                                     "ERROR")
                        print(":: MODULO PADRON " + str(
                            padronCodigo) + ": " + padronNombreApellido +"(Cuit: "+str(padronCuit)+ ") :: Error codigo: " + str(
                            err['Code']) + " - " + str(err['Message']) + " ::")

            except zeep.exceptions.Fault as fault:
                if "Session Not Found" in str(fault):
                    print(":: ERROR :: Session Not Found. Please re-authenticate.")
                    # Handle re-authentication or prompt for a new token
                else:
                    print(f":: 1 ERROR :: {fault}")
            except Exception as e:
                print(f":: 2 ERROR :: {e}")




    def main(self, operador, idLlamada=0):
        self.operador = str(operador)
        self.idLlamada = idLlamada
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

                        self.tokenGiro = GiroAuthenticate.traerTokenGiro(self)
                        print(":: TOKEN GIRO ES VALIDO: " + self.tokenGiro + " :: " + str(respLoginTokenMode) + " :: "+self.tokenGiro)
                        self.tomarDatosybase(0, plantaCodigo)
                        self.persistirEnGiro(self.datosPadronParaGiro)
                    else:
                        # Usuario o clave de giros incorrectos
                        return False



                #print(":: TODOS LOS PROCESOS FUERON COMPLETADOS ::")

                self.conn.close()
            else:
                print(":: ERROR :: TOKEN DE ACCESO INVÁLIDO. (consulte con el administrador del sistema)")

    def _create_soap_client_farm(self):

        cursor = self.conn.cursor()
        sql = "SELECT valor from giro_parametros where grupo = 'farm' and nombreParametro in ('url_farm_padron')"
        cursor.execute(sql)
        item = cursor.fetchall()
        for urlFarm in item[0]:
            url_login = urlFarm
            print(":: urlFarm: ---------> " + url_login)
        session = Session()
        session.verify = False  # Disable SSL certificate verification
        transport = Transport(session=session)
        return zeep.Client(wsdl=url_login, transport=transport)


if __name__ == "__main__":
    giros_padron = GirosPadron()
    giros_padron.main("DBA", 12345)

