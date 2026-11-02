from hoop.materiais.fases import FaseCondutividade, tensor_eshelby_condutividade
from hoop.materiais.materiais import Materiais
import numpy as np


class Condutividade(Materiais):
    def __init__(self):
        super().__init__()
        self.K = None  # Tensor de condutividade térmica
        self.k11 = None  # Condutividade térmica k11
        self.k22 = None  # Condutividade térmica k22
        self.k33 = None  # Condutividade térmica k33
        self.S = None  # Tensor de Eshelby para condutividade térmica

    def definir_tipo(self):
        self.matTipo = 'isotropico'

    def calc(self):
        self.tensorK()
        self.tensorS()

    def tensorK(self):
        self.K = np.diag([self.k11, self.k22, self.k33]).astype(float)
        return self.K

    def tensorS(self):
        self.S = tensor_eshelby_condutividade(self.geo)
        return self.S

    def como_fase(self):
        """Esta fase como objeto de valor imutável da API sem estado."""
        return FaseCondutividade(k11=self.k11, k22=self.k22, k33=self.k33)

