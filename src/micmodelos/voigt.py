from micmodelos.micmodelos import Micmodelos
from micmodelos.protocolos import ModeloMecanico, ModeloCondutividade


class Voigt(Micmodelos, ModeloMecanico, ModeloCondutividade):
    """Limite superior de Voigt: média das rigidezes ponderada pelas frações."""

    def __init__(self):
        super().__init__()
        self.tipo = 'Voigt'

    def calc_mecanico(self, objH):
        self._ler_fases_mecanicas(objH)
        fi = self.fi
        self._registrar_tensor_mecanico(fi * self.Ci + (1 - fi) * self.Cm)

    def calc_condutividade(self, objH):
        self._ler_fases_condutividade(objH)
        fi = self.fi
        self._registrar_tensor_condutividade(fi * self.Ki + (1 - fi) * self.Km)
