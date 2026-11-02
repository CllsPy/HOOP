from hoop.micmodelos.micmodelos import Micmodelos
from hoop.micmodelos.protocolos import ModeloMecanico, ModeloCondutividade


def media_voigt(fi, Xi, Xm):
    """Média aritmética das rigidezes (ou condutividades) ponderada pelas frações."""
    return fi * Xi + (1 - fi) * Xm


class Voigt(Micmodelos, ModeloMecanico, ModeloCondutividade):
    """Limite superior de Voigt: média das rigidezes ponderada pelas frações."""

    def __init__(self):
        super().__init__()
        self.tipo = 'Voigt'

    def homogeneizar(self, composito):
        C = media_voigt(composito.fi, composito.inclusao.L, composito.matriz.L)
        return self._resultado_do_tensor(composito, C)

    def homogeneizar_condutividade(self, composito):
        kh = media_voigt(composito.fi, composito.inclusao.K, composito.matriz.K)
        return self._resultado_condutividade(composito, kh)
