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
                "codigo_docu, padron_docnro, padron_ivacon, interes_tasa, padron_jncnro, padron_gananc, "
                "padron_apinro, padron_zonnro, padron_catego, padron_jubila, padron_cuit11, padron_cuil11, "
                "padron_busco1, padron_busco2, padron_observa FROM v_giro_ctacte_padron   order by padron_codigo asc")
        else:
            cursor.execute(
                "SELECT padron_codigo, padron_apelli, padron_nombre, padron_domici, padron_domnro, padron_domdto, "
                "padron_dompis, codigo_postal, padron_telcar, padron_telnro, padron_actanr, padron_ingres, "
                "codigo_docu, padron_docnro, padron_ivacon, interes_tasa, padron_jncnro, padron_gananc, "
                "padron_apinro, padron_zonnro, padron_catego, padron_jubila, padron_cuit11, padron_cuil11, "
                "padron_busco1, padron_busco2, padron_observa FROM v_giro_ctacte_padron where padron_codigo =  " + str(
                    codigo) + " order by padron asc")
        socios = cursor.fetchall()

        if len(socios) > 0:
            for a in socios:
                padronCodigo = a.padron_codigo
                padronNombreApellido = a.padron_apelli + " " + a.padron_nombre
                padronDomicilio = a.padron_domici
                padronDomicilioNro = a.padron_domnro
                padronDomicilioDpto = a.padron_domdto
                padronCodigoPostal = a.codigo_postal
                padronTelCar = a.padron_telcar
                padronTelNro = a.padron_telnro
                padronIngreso = a.padron_ingres
                padronNroDocumento = a.padron_docnro
                padronCondicionIva = a.padron_ivacon
                padronJnrNro = a.padron_jncnro
                padronGanancias = a.padron_gananc
                padronApiNro = a.padron_apinro
                padronZonaNro = a.padron_zonnro
                padronCategoria = a.padron_catego
                padronJubilacion = a.padron_jubila
                padronCuit11 = a.padron_cuit11
                padronCuil11 = a.padron_cuil11
                padronObserva = a.padron_observa

                self.datosPadron.append(
                    [padronCodigo, padronNombreApellido, padronDomicilio, padronNroDocumento, padronCodigoPostal,
                     padronCondicionIva, padronGanancias, padronApiNro, padronCategoria, padronJubilacion, padronCuit11,
                     padronObserva])

            print(":: MODULO PADRON :: DATOS RECUPERADOS ::")
        # EJECUTO CLASE clases/padronGiro que implementa el web service con giro y le informa el padronIngreso

        else:
            print("La busqueda no arrojo resultados")
        return self.datosPadron


    def procesarDatosPadronSybase(self, datosPadron, cliente):
        breakpoint()
        for padron in datosPadron:
            nombreApellido = padron[1]
            print(nombreApellido)
            #aca en datosPadronParaGiro le preparo los datos masticados para enviar a giro
            # datosPadronParaGiro.append([cliente, cuenta, clave, nombreApellido,1,0, mail,0, saldo,  saldoGeneral, saldoDif, saldoUss,saldoGeneralDolar, saldoDiferidoDolar, str(fechaHoy), marcaCambio, 3])
            # datosNuevos = datosPadronNuevos

            # persistirUsuarios(datos_nuevos, cliente)


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


    def enviarMail(self, mensaje):
        cursor = self.conn.cursor()
        cursor.execute("SELECT emp_descri, emp_descri1 FROM empresas where emp_codigo = 1")
        empresa = cursor.fetchone()
        nombreEmpresa = empresa[0]
        enviaEmail = "no-reply@kernelinformatica.com.ar"
        recibeEmail = "sistemas@kernelinformatica.com.ar"
        email_subject = ':: Kernel Sincronización con Giros :: ' + nombreEmpresa
        mensajeFull = (mensaje)
        sender_email_address = enviaEmail
        receiver_email_address = recibeEmail
        msg = EmailMessage()
        msg.set_content(mensajeFull)
        msg['Subject'] = email_subject
        msg['From'] = sender_email_address
        msg['To'] = receiver_email_address

        with smtplib.SMTP("mail.kernelinformatica.com.ar", 587) as smtp:
            smtp.starttls()
            smtp.login(sender_email_address, 'Humb3rt01')
            smtp.send_message(msg)
            # print(":: CORREO ENVIADO CON EXITO :: ")

    def persistirPadronEnGiro(self, padronParaGiro, cliente, tokenGiro):
        breakpoint()



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

                    tokenGiro = giro.get("userToken")
                    respLoginGiroSucceeded = giro.get("LoginSucceeded")
                    respLoginGiroResultCode = giro.get("resultCode")
                    respLoginTokenMode = giro.get("status")
                    if respLoginGiroSucceeded == 'true' and respLoginGiroResultCode == "600":
                        print(":: TOKEN GIRO ES VALIDO: "+tokenGiro+" :: "+str(respLoginTokenMode)+" ::")

                        self.tomarDatosPadronSybase(0, plantaCodigo)
                        self.procesarDatosPadronSybase(self.datosPadron, cli)
                        self.persistirPadronEnGiro(self, self.datosPadronParaGiro, cli, tokenGiro )
                    else:
                        # Usuario o clave de giros incorrectos
                        return False



                #print(":: TODOS LOS PROCESOS FUERON COMPLETADOS ::")
                self.enviarMail(":: KERNEL SINCRO CON GIROS :: EXPORTACION DE PADRON A GIROS ::")
                self.conn.close()
            else:
                print(":: ERROR :: TOKEN DE ACCESO INVÁLIDO. (consulte con el administrador del sistema)")


if __name__ == "__main__":
    giros_padron = GirosPadron()
    giros_padron.main()

