from materiais.materiais import Materiais
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
        if self.geo != 'esfera':
            raise NotImplementedError(
                f"Tensor de Eshelby de condutividade não implementado para a geometria "
                f"'{self.geo}'. Geometrias suportadas: 'esfera'."
            )
        self.S = np.eye(3) / 3
        return self.S
