from hoop.materiais.fases import FaseMecanica
from hoop.materiais.materiais import Materiais
from hoop.mecanico.geometria_registry import GeometriaRegistry, tensor_eshelby
from hoop.mecanico.tensores import tensor_rigidez_isotropico, tensor_hill_esfera


class Mecanico(Materiais):
    def __init__(self):
        super().__init__()
        self.E = None  # Módulo de Elasticidade
        self.v = None  # Coeficiente de Poisson
        self.L = None  # Tensor constitutivo
        self.P = None  # Tensor de Hill
        self.S = None  # Tensor de Eshelby

    def definir_tipo(self):
        self.matTipo = 'isotropico'

    def calc(self):
        self.tensorL()
        self.tensorP()
        self.tensorS()

    def tensorL(self):
        self.L = tensor_rigidez_isotropico(self.E, self.v)

    def tensorP(self):
        self.P = tensor_hill_esfera(self.E, self.v)

    def tensorS(self):
        geometria = GeometriaRegistry.obter(self.geo)
        self.S = geometria.calcular_S(self.E, self.v, self.P, self.L)
        return self.S

    @staticmethod
    def montaL(E, v):
        return tensor_rigidez_isotropico(E, v)

    def montaS(self, E, v):
        """Tensor de Eshelby para um meio (E, v) com a geometria deste material."""
        return tensor_eshelby(self.geo, E, v)

    def como_fase(self):
        """Esta fase como objeto de valor imutável da API sem estado."""
        return FaseMecanica(E=self.E, v=self.v)
