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




class GiroAuthenticate(DBConnection):

    def __init__(self):
        super().__init__()
        #self.conn = self.create_connection()


        self.config = []
        self.resp = []
        self.client = self._create_soap_client()
        fechaHoraHoyTemp = datetime.now()
        formatoFechaHoy = "%Y-%m-%d %H:%M:%S"
        self.fechaHoraHoy = fechaHoraHoyTemp.strftime(formatoFechaHoy)
        self.pedirTokenAcceso()

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
                self.resp.append({'userToken': tokenUsuario,
                                  'resultCode': '600',
                                  'LoginSucceeded': 'true',
                                  'loginDate': fechaDesde,
                                  'domain': domain,
                                  'fechaDesde': fechaDesde,
                                  'fechaHasta': fechaHasta,
                                  'status': status + tokenUsuario})

            print(":: TOKEN :: "+str(tokenUsuario))
            tokenGiroStatus = self.verificoSiHayTokenVigenteEnGiro(self, tokenUsuario)
            if tokenGiroStatus == True:
                return self.resp
            else:
                return self.pedirTokenAcceso(self, 1)

        else:
            print(":: NO HAY TOKEN VIGENTE, SE DEBE SOLICITAR UNO NUEVO A GIROS ::")
            return False


    def _create_soap_client(self):
        cursor = self.conn.cursor()
        sql = "SELECT valor from giro_parametros where grupo = 'login' and nombreParametro in ('url_login')"
        cursor.execute(sql)
        item = cursor.fetchall()
        for urlLogin in item[0]:
            url_login = urlLogin


        session = Session()
        session.verify = False  # Disable SSL certificate verification
        transport = Transport(session=session)
        return zeep.Client(wsdl=url_login, transport=transport)


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
        print(":: MODULO PADRON :: PERSISTIR USUARIOS ::")
        # Valido token primero, armo parametros para enviar para consultar token
        paramsToken = {
            'token': tokenGiro,

        }
        tokenResp = self.client.service.ValidarToken(**paramsToken)
        if tokenResp['LoginSucceeded'] == 'true':
            print("Token vigente, continuo con el proceso")
        else:
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

                    self.resp.append([0, result_code, login_succeeded, 0, 0, 'error'])

                else:
                    user_token = root.find('UserToken').text
                    login_date = root.find('LoginDate').text
                    domain = root.find('Domains/Domain').text

                    #fechaLogin = datetime.fromisoformat(login_date[:-6])
                    #fechaLogin_str = fechaLogin.strftime('%Y-%m-%d %H:%M:%S')
                    fechaActual = datetime.now()
                    # Definir un timedelta con las horas que quieres sumar
                    #orasAsumar = fechaActual + timedelta(hours=6)
                    #fechaLogin_str_hasta =  horasAsumar
                    self.resp.append({'userToken': user_token,
                                      'resultCode': result_code,
                                      'LoginSucceeded': login_succeeded,
                                      'loginDate': login_date,
                                      'domain': domain,
                                      'fechaDesde': login_date,
                                      'fechaHasta': login_date,
                                      'status': 'Nuevo Token otorgado ' + user_token})
                    cursor = self.conn.cursor()
                    sql= "update giro_accesos set domain = " + str(domain) + " , token = " + str(user_token) + " , fechaCreacion = " + str(datetime.now()) + " , fechaDesde = " + str(fechaLogin_str) + " , fechaHasta = " + str(fechaLogin_str_hasta) + " , tokenTipo = " + str('md5') + " where idAcceso = 1"
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

    # data = client.pedirTokenAcceso()



