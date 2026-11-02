import numpy as np

from hoop.micmodelos.micmodelos import Micmodelos
from hoop.micmodelos.protocolos import ModeloMecanico, ModeloCondutividade


def suspensao_diluida(fi, Xi, Xm, S):
    """Xm + fi (Xi - Xm) A, com A = [I + S Xm^-1 (Xi - Xm)]^-1 (concentração de Eshelby)."""
    I = np.eye(Xm.shape[0])
    A = np.linalg.inv(I + np.dot(S, np.dot(np.linalg.inv(Xm), Xi - Xm)))
    return Xm + fi * np.dot(Xi - Xm, A)


class DiluteSuspension(Micmodelos, ModeloMecanico, ModeloCondutividade):
    def __init__(self):
        super().__init__()
        self.tipo = 'Dilute Suspension'

    def homogeneizar(self, composito):
        C = suspensao_diluida(composito.fi, composito.inclusao.L, composito.matriz.L,
                              composito.eshelby)
        return self._resultado_do_tensor(composito, C)

    def homogeneizar_condutividade(self, composito):
        kh = suspensao_diluida(composito.fi, composito.inclusao.K, composito.matriz.K,
                               composito.eshelby)
        return self._resultado_condutividade(composito, kh)
