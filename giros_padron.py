# The common XML.RPC endpoint
import smtplib
from datetime import datetime
from email.message import EmailMessage

import zeep
from requests import Session
from zeep.transports import Transport
from conn.DBConnection import DBConnection as DBConnection
from giros_authenticate import GiroAuthenticate as GiroAuthenticate





class GirosPadron(DBConnection):
    def __init__(self):
        super().__init__()
        self.tokenGiro = "";
        self.config = []
        self.resp = []
        self.client = self._create_soap_client_farm()
        self.hoy = datetime.now()
        self.maskCuenta = "0000000"
        self.datosPadron = []
        self.datosPadronParaGiro = []

    def tomarDatosPadronSybase(self, codigo, plantaCodigo):

        print(":: MODULO PADRON :: Aguarde un momento por favor ...")
        global datos
        cursor = self.conn.cursor()
        if codigo == 0:
            cursor.execute(
                "SELECT  padron_codigo, padron_apelli, padron_nombre, padron_domici, padron_domnro, padron_domdto, "
                "padron_dompis, codigo_postal, padron_telcar, padron_telnro, padron_actanr, padron_ingres, "
                "codigo_docu, padron_docnro, padron_ivacon, desc_cond_iva, interes_tasa, padron_jncnro, padron_gananc, "
                "padron_apinro, padron_zonnro, padron_catego, catego_descri, padron_jubila, padron_cuit11, padron_cuil11, "
                "padron_busco1, padron_busco2, padron_observa, provincia, localidad, provincia_codigo FROM v_giro_ctacte_padron   order by padron_codigo asc")
        else:
            cursor.execute(
                "SELECT padron_codigo, padron_apelli, padron_nombre, padron_domici, padron_domnro, padron_domdto, "
                "padron_dompis, codigo_postal, padron_telcar, padron_telnro, padron_actanr, padron_ingres, "
                "codigo_docu, padron_docnro, padron_ivacon, desc_cond_iva,  interes_tasa, padron_jncnro, padron_gananc, "
                "padron_apinro, padron_zonnro, padron_catego, catego_descri, padron_jubila, padron_cuit11, padron_cuil11, "
                "padron_busco1, padron_busco2, padron_observa, provincia, localidad, provincia_codigo FROM v_giro_ctacte_padron where padron_codigo =  " + str(
                    codigo) + " order by padron asc")
        socios = cursor.fetchall()

        if len(socios) > 0:
            for a in socios:
                padronCodigo = a.padron_codigo
                padronNombreApellido = a.padron_apelli + " " + a.padron_nombre
                padronDomicilio = str(a.padron_domici)+" "+str(a.padron_domnro)+" "+str(a.padron_domdto)
                padronCodigoPostal = a.codigo_postal
                padronProvinciaNombre = a.provincia
                padronProvinciaCodigo = a.provincia_codigo
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
                padronCategoriaNombre = a.catego_descri
                padronJubilacion = a.padron_jubila
                if  a.padron_cuit11 == None:
                    padronCuit = a.padron_cuil11
                else:
                    padronCuit = a.padron_cuit11
                padronObserva = a.padron_observa
                # padronTipoCuenta: Giro define este valor como INTERNA = 1 o EXTERNA = 2
                padronTipoCuenta = 1
                self.datosPadronParaGiro.append(
                    [padronNombreApellido, padronCondicionIva, padronCodigoPostal, padronCuit, padronDomicilio, padronLocalidadNombre, "ARGENTINA", padronProvinciaNombre, padronTipoCuenta])

            print(":: MODULO PADRON :: DATOS RECUPERADOS ::")
        # EJECUTO CLASE clases/padronGiro que implementa el web service con giro y le informa el padronIngreso

        else:
            print("La busqueda no arrojo resultados")
        return self.datosPadron






    def _create_soap_client_farm(self):

        cursor = self.conn.cursor()
        sql = "SELECT valor from giro_parametros where grupo = 'login' and nombreParametro in ('url_farm')"
        cursor.execute(sql)
        item = cursor.fetchall()
        for urlFarm in item[0]:
            url_login = urlFarm
        session = Session()
        session.verify = False  # Disable SSL certificate verification
        transport = Transport(session=session)
        return zeep.Client(wsdl=url_login, transport=transport)



    def persistirPadronEnGiro(self, padronParaGiro, cliente):




        '''
         u =0
        for cliente, cuenta, clave, nombreApellido,tipoDocumento,nroDocumento, mail,telefono, saldo,  saldoGeneral, saldoDif, saldoUss,saldoGeneralDolar, saldoDiferidoDolar, fecha, marcaCambio, tipoUsuario in datos:

            cursor = conn.gestagro.conn.cursor()
            cursor.execute("select * from usuarios where coope= "+str(cliente)+" and cuenta ="+str(cuenta)+" and marca_cambio > 0 ")
            resu = cursor.fetchone()

            if resu == None:
               try:
                   cursor.execute(
                       "insert into usuarios(coope,  cuenta,clave, nombre, tipoDocumento, nroDocumento, mail, telefono, saldo, saldoGral, saldoDif, saldoDolar, saldoGralDolar, saldoDifDolar, fecha, marca_cambio, tipoUsuario,  ultActualizacion) values('" + cliente + "', '" + cuenta + "', MD5('" + clave + "'), '" + nombreApellido + "',  '" + str(
                           tipoDocumento) + "' , '" + str(nroDocumento) + "', '" + mail + "',  '" + str(
                           telefono) + "', '" + str(saldo) + "', '" + str(saldoGeneral) + "', '" + str(
                           saldoDif) + "', '" + str(saldoUss) + "', '" + str(saldoGeneralDolar) + "', '" + str(
                           saldoDiferidoDolar) + "', '" + str(fecha) + "', '" + str(marcaCambio) + "', '" + str(
                           tipoUsuario) + "', now() )")
                   conn.gestagro.conn.commit()
                   print("Socio " + str(cuenta) + " - " + str(nombreApellido) + " agregado !!! - Saldo: "+str(saldo))
               except Exception as e:
                   print(f"Error al ejecutar la consulta: {e}")
                   enviarMail("Modulo Usuarios, se ha producido un error al agregar un usuario: " + str(e))
                   conn.gestagro.conn.commit()
                   conn.gestagro.conn.commit()
                   cursorControl = conn.gestagro.conn.cursor()

                   cursorControl.execute(
                       "INSERT INTO gestAgroProcesosLogs(coope, resultado, estado, descripcion, origen, fecha, control) VALUES('" + str(
                           cliente) + "', '" + str("usuarios") + "', '" + "ERROR" + "', '" + str(
                           str(e)) + "' , '" + str("api:gestagroSincro") + "', NOW(), NOW());")

            else:
                cursor.execute("update usuarios set saldo = '"+str(saldo)+"', saldoGral = '"+str(saldoGeneral)+"', saldoDif = '"+str(saldoDif)+"', saldoDolar = '"+str(saldoUss)+"', saldoGralDolar= '"+str(saldoGeneralDolar)+"', saldoDifDolar= '"+str(saldoDiferidoDolar)+"', fecha= '"+str(fecha)+"' , ultActualizacion = now(), nombre= '"+str(nombreApellido)+"' where coope = '"+cliente+"' and cuenta = '"+cuenta+"'")
                conn.gestagro.conn.commit()
                print("Socio "+str(cuenta)+" - "+str(nombreApellido)+" actualizado !! - Saldo: "+str(saldo))

            u = u+1

        cursorControl = conn.gestagro.conn.cursor()
        cursorControl.execute(
            "INSERT INTO gestAgroProcesosLogs(coope, resultado, estado, descripcion, origen, fecha, control) VALUES('" + str(
                cliente) + "', '" + str("usuarios") + "', '"+ str("OK")+"','" +
             str("Usuarios Procesados :: " + str(u)) + "' , '" + str(
                "api:gestagroSincro") + "', NOW(), NOW());")
    '''
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

                    respLoginGiroSucceeded = giro.get("LoginSucceeded")
                    respLoginGiroResultCode = giro.get("resultCode")
                    respLoginTokenMode = giro.get("status")
                    if respLoginGiroSucceeded == 'true' and respLoginGiroResultCode == "600":

                        self.tokenGiro = GiroAuthenticate.traerTokenGiro(self)
                        print(":: TOKEN GIRO ES VALIDO: " + self.tokenGiro + " :: " + str(respLoginTokenMode) + " :: "+self.tokenGiro)
                        self.tomarDatosPadronSybase(0, plantaCodigo)
                        self.persistirPadronEnGiro(self.datosPadronParaGiro, cli)
                    else:
                        # Usuario o clave de giros incorrectos
                        return False



                #print(":: TODOS LOS PROCESOS FUERON COMPLETADOS ::")

                self.conn.close()
            else:
                print(":: ERROR :: TOKEN DE ACCESO INVÁLIDO. (consulte con el administrador del sistema)")


if __name__ == "__main__":
    giros_padron = GirosPadron()
    giros_padron.main()

