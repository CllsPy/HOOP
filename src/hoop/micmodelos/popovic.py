from hoop.micmodelos.micmodelos import Micmodelos
from hoop.micmodelos.protocolos import ModeloMecanico, ModeloCondutividade
from hoop.micmodelos.reuss import media_reuss
from hoop.micmodelos.voigt import media_voigt


def media_popovic(fi, Xi, Xm):
    """Média aritmética entre os limites de Voigt e de Reuss."""
    return (1 / 2) * (media_reuss(fi, Xi, Xm) + media_voigt(fi, Xi, Xm))


class Popovic(Micmodelos, ModeloMecanico, ModeloCondutividade):
    def __init__(self):
        super().__init__()
        self.tipo = 'popovic'

    def homogeneizar(self, composito):
        C = media_popovic(composito.fi, composito.inclusao.L, composito.matriz.L)
        return self._resultado_do_tensor(composito, C)

    def homogeneizar_condutividade(self, composito):
        kh = media_popovic(composito.fi, composito.inclusao.K, composito.matriz.K)
        return self._resultado_condutividade(composito, kh)
