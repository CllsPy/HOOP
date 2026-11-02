import numpy as np

from hoop.micmodelos.micmodelos import Micmodelos
from hoop.micmodelos.protocolos import ModeloMecanico, ModeloCondutividade


def media_reuss(fi, Xi, Xm):
    """Média harmônica (matricial) de Reuss: (fi Xi^-1 + (1 - fi) Xm^-1)^-1."""
    return np.linalg.inv(fi * np.linalg.inv(Xi) + (1 - fi) * np.linalg.inv(Xm))


class Reuss(Micmodelos, ModeloMecanico, ModeloCondutividade):
    """Limite inferior de Reuss: média das flexibilidades ponderada pelas frações."""

    def __init__(self):
        super().__init__()
        self.tipo = 'Reuss'

    def homogeneizar(self, composito):
        self._exigir_inclusao_com_rigidez(composito, 'Reuss', 'o resultado é nulo')
        C = media_reuss(composito.fi, composito.inclusao.L, composito.matriz.L)
        return self._resultado_do_tensor(composito, C)

    def homogeneizar_condutividade(self, composito):
        kh = media_reuss(composito.fi, composito.inclusao.K, composito.matriz.K)
        return self._resultado_condutividade(composito, kh)
