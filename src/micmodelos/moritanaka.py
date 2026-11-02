import numpy as np
from scipy.linalg import inv

from micmodelos.micmodelos import Micmodelos
from micmodelos.protocolos import ModeloMecanico, ModeloCondutividade


class MoriTanaka(Micmodelos, ModeloMecanico, ModeloCondutividade):
    def __init__(self):
        super().__init__()
        self.tipo = "Mori-Tanaka"

    def calc_mecanico(self, objH):
        self._ler_fases_mecanicas(objH)
        fi, Cm, Ci = self.fi, self.Cm, self.Ci
        S = objH.matH[0].S
        I = np.eye(Cm.shape[0])

        T = inv(inv(Cm - Ci) @ Cm - S)
        C = Cm @ (I + fi * (S - I) @ T) @ inv(I + fi * S @ T)
        self._registrar_tensor_mecanico(C)

    def calc_condutividade(self, objH):
        self._ler_fases_condutividade(objH)
        fi, Km, Ki = self.fi, self.Km, self.Ki
        S = objH.matH[0].S
        I = np.eye(Km.shape[0])

        T = inv((np.linalg.inv(Km - Ki) @ Km) - S)
        kh = Km @ (I + fi * (S - I) @ T) @ inv(I + fi * S @ T)
        self._registrar_tensor_condutividade(kh)
