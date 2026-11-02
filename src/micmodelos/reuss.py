import numpy as np

from micmodelos.micmodelos import Micmodelos
from micmodelos.protocolos import ModeloMecanico, ModeloCondutividade


def media_reuss(fi, Xi, Xm):
    """Média harmônica (matricial) de Reuss: (fi Xi^-1 + (1 - fi) Xm^-1)^-1."""
    return np.linalg.inv(fi * np.linalg.inv(Xi) + (1 - fi) * np.linalg.inv(Xm))


class Reuss(Micmodelos, ModeloMecanico, ModeloCondutividade):
    """Limite inferior de Reuss: média das flexibilidades ponderada pelas frações."""

    def __init__(self):
        super().__init__()
        self.tipo = 'Reuss'

    def calc_mecanico(self, objH):
        self._ler_fases_mecanicas(objH)
        self._registrar_tensor_mecanico(media_reuss(self.fi, self.Ci, self.Cm))

    def calc_condutividade(self, objH):
        self._ler_fases_condutividade(objH)
        self._registrar_tensor_condutividade(media_reuss(self.fi, self.Ki, self.Km))
