# File: main_class.py

from giros_transporte_chasis import GiroTransporteChasis
from giros_transporte_acoplado  import GiroTransporteAcoplado
from giros_obtener_registros import  GirosObtenerRegistros
from giros_padron import GirosPadron
import sys

class MainClass:
    def __init__(self):

        self.padron = GirosPadron
        self.chasis = GiroTransporteChasis()
        self.acoplados = GiroTransporteAcoplado()
        self.registros = GirosObtenerRegistros()

    def chasis(self, param):
        result = self.chasis()
        return result

    def acoplados(self, param):
        result = self.acoplados()
        return result

    def padron(self, param):
        result = self.padron()
        return result

if __name__ == "__main__":

    argumentos = sys.argv
    if len(argumentos) > 0:
        # Recibo los argumentos
        opcion = argumentos[1]
        # Decido que ejecuto
        if opcion == 1:
            main = MainClass()
            result = main.chasis.main()
        elif opcion == 2:
            main = MainClass()
            result = main.acoplados.main()
        elif opcion == 3:
            main = MainClass()
            result = main.padron.main()
        elif opcion == 4:
            main = MainClass()
            result = main.registros.main()
        else:
            print(":: Giro Base :: Opción inválida, no hay argumentos.")
