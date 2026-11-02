from micmodelos.micmodelos import Micmodelos
from micmodelos.protocolos import ModeloMecanico, ModeloCondutividade
from micmodelos.reuss import media_reuss


def media_popovic(fi, Xi, Xm):
    """Média aritmética entre os limites de Voigt e de Reuss."""
    voigt = fi * Xi + (1 - fi) * Xm
    return (1 / 2) * (media_reuss(fi, Xi, Xm) + voigt)


class Popovic(Micmodelos, ModeloMecanico, ModeloCondutividade):
    def __init__(self):
        super().__init__()
        self.tipo = 'popovic'

    def calc_mecanico(self, objH):
        self._ler_fases_mecanicas(objH)
        self._registrar_tensor_mecanico(media_popovic(self.fi, self.Ci, self.Cm))

    def calc_condutividade(self, objH):
        self._ler_fases_condutividade(objH)
        self._registrar_tensor_condutividade(media_popovic(self.fi, self.Ki, self.Km))
