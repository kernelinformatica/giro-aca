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
import errores
import respuestas




class GiroAuthenticate(DBConnection):

    def __init__(self):
        super().__init__()
        self.config = []
        self.resp = []
        self.client = self._create_soap_client_login()
        self.clientFarm = self._create_soap_client_farm()
        fechaHoraHoyTemp = datetime.now()
        formatoFechaHoy = "%Y-%m-%d %H:%M:%S"
        self.fechaHoraHoy = fechaHoraHoyTemp.strftime(formatoFechaHoy)
        self.pedirTokenAcceso(0)

    def verificoSiHayTokenVigenteSybase(self):

        cursor = self.conn.cursor()
        sql = "SELECT idAcceso, domain, token, tokenTipo, fechaCreacion,  fechaDesde, fechaHasta fechaHasta FROM giro_accesos where idAcceso = 1"
        cursor.execute(sql)
        token = cursor.fetchall()
        if len(token) >  0:

            for row in token:
                idAcceso = row.idAcceso
                tokenUsuario = row.token
                tokenTipo = row.tokenTipo
                domain = row.domain
                fechaCreacion = row.fechaCreacion
                fechaDesde = row.fechaDesde
                fechaHasta = row.fechaHasta
                tokenStatus = True
                status = "."


            print(":: TOKEN :: "+str(tokenUsuario))

            tokenGiroStatus = self.verificoSiHayTokenVigenteEnGiro(tokenUsuario)

            if tokenGiroStatus == True:
                self.resp.append({'userToken': tokenUsuario,
                                  'resultCode': '600',
                                  'LoginSucceeded': 'true',
                                  'loginDate': fechaDesde,
                                  'domain': domain,
                                  'fechaDesde': fechaDesde,
                                  'fechaHasta': fechaHasta,
                                  'status': status + tokenUsuario})
                return self.resp
            else:
                return self.pedirTokenAcceso(1)

        else:
            print(":: NO HAY TOKEN VIGENTE, SE DEBE SOLICITAR UNO NUEVO A GIROS ::")
            return False

    def traerTokenGiro(self):
        cursor = self.conn.cursor()
        sql = "SELECT token FROM giro_accesos where idAcceso = 1"
        cursor.execute(sql)
        item = cursor.fetchall()
        for items in item[0]:
            tok = items
        return tok


    def _create_soap_client_login(self):
       cursor = self.conn.cursor()
       sql = "SELECT valor from giro_parametros where grupo = 'login' and nombreParametro in ('url_login')"
       cursor.execute(sql)
       item = cursor.fetchall()
       for items in item[0]:
           url = items
       session = Session()
       session.verify = False  # Disable SSL certificate verification
       transport = Transport(session=session)
       return zeep.Client(wsdl=url, transport=transport)

    def _create_soap_client_farm(self):
       cursor = self.conn.cursor()
       sql = "SELECT valor from giro_parametros where grupo = 'farm' and nombreParametro in ('url_farm')"
       cursor.execute(sql)
       item = cursor.fetchall()
       for items in item[0]:
           url = items
       session = Session()
       session.verify = False  # Disable SSL certificate verification
       transport = Transport(session=session)
       return zeep.Client(wsdl=url, transport=transport)

    def configuracion(self):
        cursor = self.conn.cursor()
        sql = "SELECT valor from giro_parametros where grupo = 'login' and nombreParametro in ('url_login', 'ws_usuario', 'ws_clave', 'domain','packname', 'usuario', 'clave') "
        cursor.execute(sql)
        conf = cursor.fetchall()

        if len(conf) > 0:
            for a in conf:
                url = conf[0].valor
                usu_ws = conf[1].valor
                cla_ws = conf[2].valor
                dom =  conf[4].valor
                pack = conf[3].valor
                usu = conf[5].valor
                cla = conf[6].valor
                params = {
                    'packName': str(pack),
                    'domain': str(dom),
                    'userName': str(usu),
                    'userPwd': str(cla),
                }
            return params

    def verificoSiHayTokenVigenteEnGiro(self, tokenGiro):
         # Valido token primero, armo parametros para enviar para consultar token
        paramsToken = {
            'Token': tokenGiro,

        }
        self.clientFarm.transport.http_post = True  # Para usar POST
        self.clientFarm.transport.http_get = False  # Para desactivar GET
        tokenResp = self.clientFarm.service.ValidarToken(**paramsToken)
        if tokenResp['CodigoError'] == 0:
            print("El token utilizado es válido en giro.")
            return True
        else:
            return False
            print("Token invalido o vencido, solicito nuevo token")



    def pedirTokenAcceso(self, op):
        # op = 0 verifica token,
        # op = 1 renueva token
        if op == 0:
            tokenVigente  = self.verificoSiHayTokenVigenteSybase()
        else:
            tokenVigente = False


        if tokenVigente == False:
            #traigo los parmetreos de la tabla para setear los parametros
            parametros = self.configuracion()
            response = self.client.service.LoginServiceWithPackDirect(**parametros)

            if response == None:
                print(":: El servicio web no respondió u ocurrió un error inesperado, intente nuevamente más tarde ::")
            else:


                root = ET.fromstring(response)
                # Access and print the desired values
                login_succeeded = root.find('LoginSucceeded').text
                result_code = root.find('ResultCode').text
                print(":: Giro Web Service SessionManager.LoginServiceWithPackDirect() :: "+str(login_succeeded))
                if login_succeeded == "false":
                    print(":: LA autentificacion falló, usuario o clave incorrectos ::")
                    codigoError = root.find('ResultCode').text
                    descripcionError =login_succeeded
                    nroTicket = 0
                    nroCarta = 0
                    '''
                     resp = respuestas.GrabaRespuestas()
                    resp.grabarRespuesta(codigoError, descripcionError, 0, 0, 2, "ValidarToken",".", 'N', 0, "Usuario o clave incorrectos", "ERROR")

                    '''
                else:
                    user_token = root.find('UserToken').text
                    login_date = root.find('LoginDate').text
                    domain = root.find('Domains/Domain').text

                    fechaLogin = datetime.fromisoformat(login_date[:-6])
                    fechaLogin_str = fechaLogin.strftime('%Y-%m-%d %H:%M:%S')
                    fechaActual = datetime.now()
                    # Definir un timedelta con las horas que quieres sumar
                    horasAsumar = fechaActual + timedelta(hours=6)
                    fechaLogin_str_hasta =  horasAsumar
                    self.resp.append({'userToken': user_token,
                                      'resultCode': result_code,
                                      'LoginSucceeded': login_succeeded,
                                      'loginDate': login_date,
                                      'domain': domain,
                                      'fechaDesde': login_date,
                                      'fechaHasta': login_date,
                                      'status': 'Nuevo Token otorgado ' + user_token})
                    cursor = self.conn.cursor()
                    sql= "update giro_accesos set domain = '" + str(domain) + "' , token = '" + str(user_token) + "' , fechaCreacion = '" + str(datetime.now()) + "' , fechaDesde = '" +str(datetime.now()) + "' , fechaHasta = '" + str(datetime.now())+ "' , tokenTipo = '" + str('md5') + "' where idAcceso = 1"
                    

                    cursor.execute(sql)
                    self.conn.commit()
                    if cursor.rowcount > 0:
                        print(":: Gestion de Token Giro: Registro actualizado correctamente. ::")
                    else:
                        print(":: Gestion de Token Giro: No se actualizó ningún token. ::")
                    cursor.close()



                return self.resp



        else:
            # REUTILIZO TOKEN EXISTENTE PORQUE EXISTE Y ESTA VIGENTE
            print(":: pedirTokenAcceso() --> REUTILIZO TOKEN EXISTENTE -> ")


            return tokenVigente






if __name__ == "__main__":

    client = GiroAuthenticate()




