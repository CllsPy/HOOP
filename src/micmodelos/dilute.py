import numpy as np

from micmodelos.micmodelos import Micmodelos
from micmodelos.protocolos import ModeloMecanico, ModeloCondutividade


def suspensao_diluida(fi, Xi, Xm, S):
    """Xm + fi (Xi - Xm) A, com A = [I + S Xm^-1 (Xi - Xm)]^-1 (concentração de Eshelby)."""
    I = np.eye(Xm.shape[0])
    A = np.linalg.inv(I + np.dot(S, np.dot(np.linalg.inv(Xm), Xi - Xm)))
    return Xm + fi * np.dot(Xi - Xm, A)


class DiluteSuspension(Micmodelos, ModeloMecanico, ModeloCondutividade):
    def __init__(self):
        super().__init__()
        self.tipo = 'Dilute Suspension'

    def calc_mecanico(self, objH):
        self._ler_fases_mecanicas(objH)
        S = objH.matH[0].S
        self._registrar_tensor_mecanico(suspensao_diluida(self.fi, self.Ci, self.Cm, S))

    def calc_condutividade(self, objH):
        self._ler_fases_condutividade(objH)
        S = objH.matH[0].S
        self._registrar_tensor_condutividade(suspensao_diluida(self.fi, self.Ki, self.Km, S))
