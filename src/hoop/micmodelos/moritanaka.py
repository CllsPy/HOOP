import numpy as np

from hoop.micmodelos.micmodelos import Micmodelos
from hoop.micmodelos.protocolos import ModeloMecanico, ModeloCondutividade


def mori_tanaka(fi, Xi, Xm, S):
    """Xm + fi (Xi - Xm) [(1 - fi) B + fi I]^-1, com B = I + S Xm^-1 (Xi - Xm).

    B é o inverso do tensor de concentração de Eshelby. Esta forma não inverte
    Xm - Xi, então vale também para fases iguais ou com o mesmo cisalhamento.
    """
    I = np.eye(Xm.shape[0])
    B = I + S @ np.linalg.inv(Xm) @ (Xi - Xm)
    return Xm + fi * (Xi - Xm) @ np.linalg.inv((1 - fi) * B + fi * I)


class MoriTanaka(Micmodelos, ModeloMecanico, ModeloCondutividade):
    def __init__(self):
        super().__init__()
        self.tipo = "Mori-Tanaka"

    def homogeneizar(self, composito):
        C = mori_tanaka(composito.fi, composito.inclusao.L, composito.matriz.L,
                        composito.eshelby)
        return self._resultado_do_tensor(composito, C)

    def homogeneizar_condutividade(self, composito):
        kh = mori_tanaka(composito.fi, composito.inclusao.K, composito.matriz.K,
                         composito.eshelby)
        return self._resultado_condutividade(composito, kh)
