from materiais import Materiais
import numpy as np


class Condutividade(Materiais):
    def __init__(self):
        super().__init__()
        self.tipo= None
        self.K = None  # Tensor Condutividade Térmica
        self.k11 = None  # Condutividade Térmica k11
        self.k22 = None  # Condutividade Térmica k22
        self.k33 = None  # Condutividade Térmica k33
        self.S = None  # Tensor de Eshelby para Condutividade Térmica

    def tipo(self):
        self.matTipo = 'isotropico'

    def calc(self):
        self.tensorK()
        self.tensorS()

    def tensorK(self): #<------- FUNCIONANDO =======================>
        self.K = np.zeros((3, 3))
        self.K[0, 0] = self.k11
        self.K[1, 1] = self.k22
        self.K[2, 2] = self.k33


    def tensorS(self): #<------- FUNCIONANDO =======================
        if self.geo == 'esfera':
            self.S = np.zeros((3, 3))
            self.S[0, 0] = 1 / 3
            self.S[1, 1] = 1 / 3
            self.S[2, 2] = 1 / 3

        elif self.geo == 'cilindro':
            print("Não Existe Geometria Definida")

        elif self.geo == 'disco':
            print("Não Existe Geometria Definida")