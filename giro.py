# File: main_class.py
import random

from giros_transporte_chasis import GiroTransporteChasis
from giros_transporte_acoplado  import GiroTransporteAcoplado
from giros_obtener_registros import  GirosObtenerRegistros
from giros_localidades import GiroLocalidades
from giros_padron import GirosPadron
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import sys

class MainClass:
    def __init__(self):

        self.padron = GirosPadron
        self.chasis = GiroTransporteChasis()
        self.acoplados = GiroTransporteAcoplado()
        self.registros = GirosObtenerRegistros()
        self.localidades = GiroLocalidades()

    def execute_chasis(self, param):
        result = self.chasis.main(param)
        return result

    def execute_acoplados(self, param):
        result = self.acoplados.main(param)
        return result

    def execute_padron(self, operador, idLlamada):
        result = self.padron.main(operador, idLlamada)
        return result

    def execute_localidades(self, operador, idLlamada):
        result = self.localidades.main(operador, idLlamada)
        return result

if __name__ == "__main__":
    argumentos = sys.argv

    operacionId = "11"
    idLlamada = random.randint(1, 9999999999)
    operador = "."
    id=""

    print(argumentos)
    # if len(argumentos) > 0:
    if len(operacionId) > 0:
        # Recibo los argumentos
        """
       operacionId = argumentos[1]
       idLlamada = argumentos[2]
       operador = argumentos[3]

       
        if argumentos[4] is not None:
            id = argumentos[4]
        else:
            id = ""
         """
        # Decido que ejecuto
        if operacionId == "3":
            main = MainClass()
            result = main.chasis.main()
        elif operacionId == "7":
            main = MainClass()
            result = main.acoplados.main()
        elif operacionId == "15":
            main = MainClass()
            result = main.padron.main(operador, idLlamada)
        elif operacionId == "11":
            main = MainClass()
            result = main.registros.main(operador, idLlamada)
        elif operacionId == "12":
            main = MainClass()
            result = main.registros.main(operador, idLlamada)
        elif operacionId == "13":
            main = MainClass()
            result = main.localidades.main(operador, idLlamada)
        elif operacionId == "16":
            main = MainClass()
            result = main.localidades.eliminarLocalidad(operador, idLlamada, id)

        else:
            print(":: Giro Base :: Opción inválida, no hay argumentos.")
