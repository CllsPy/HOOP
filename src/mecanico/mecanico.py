from materiais.materiais import Materiais
import numpy as np
import math

class Mecanico (Materiais):
    # E = None    # Módulo de Elasticidade
    # v = None    # Coeficiente de Poisson
    # L = None    # Tensor de Hill
    # P = None    # Tensor de Hill
    # S = None    # Tensor de Eshelby
    # A = None    # Tensor Concentração de Tensão
    # B = None    # Tensor Concenrtação de Deformaçãov

    def __init__(self):
        super().__init__()
        self.tipo = None
        self.E = None    # Módulo de Elasticidade
        self.v = None    # Coeficiente de Poisson
        self.L = None    # Tensor de Hill
        self.P = None    # Tensor de Hill
        self.S = None    # Tensor de Eshelby
        self.A = None    # Tensor Concentração de Tensão
        self.B = None    # Tensor Concenrtação de Deformação


    def tipo(self): #<------- FUNCIONANDO =======================
        self.matTipo = 'isotropico'

    def calc(self): #<------- FUNCIONANDO =======================
        self.tensorL()
        self.tensorP()
        self.tensorS()

    def tensorL(self): #<------- FUNCIONANDO =======================
        E = self.E
        v = self.v

        c = E / ((1 + v) * (1 - 2 * v))
        x = np.array([[1-v, v, v, 0, 0, 0],
                  [v, 1-v, v, 0, 0, 0],
                  [v, v, 1-v, 0, 0, 0],
                  [0, 0, 0, (1-2*v)/2, 0, 0],
                  [0, 0, 0, 0, (1-2*v)/2, 0],
                  [0, 0, 0, 0, 0, (1-2*v)/2]])
        self.L = c*x

    def tensor_L(self, E,v): #<------- FUNCIONANDO =======================
        c = E / ((1 + v) * (1 - 2 * v))
        x = np.array([[1-v, v, v, 0, 0, 0],
                  [v, 1-v, v, 0, 0, 0],
                  [v, v, 1-v, 0, 0, 0],
                  [0, 0, 0, (1-2*v)/2, 0, 0],
                  [0, 0, 0, 0, (1-2*v)/2, 0],
                  [0, 0, 0, 0, 0, (1-2*v)/2]])
        L = c*x
        return L

    def tensorP(self): #<------- FUNCIONANDO =======================
        E = self.E
        v = self.v
        m = (1+v)/(3*(1-v))
        n = (2*(4-5*v))/(15*(1-v))
        k = E/(3*(1-2*v))
        G = E/(2*(1+v))

        self.P = np.array([[(1/3)*((m/(3*k))+(n/G)),(1/3)*((m/(3*k))-(n/(2*G))),(1/3)*((m/(3*k))-(n/(2* G))),0,0,0],
        [(1/3)*((m/(3*k))-(n/(2*G))),(1/3)*((m/(3*k))+(n/G)),(1/3)*((m/(3*k))-(n/(2*G))),0,0,0],
        [(1/3)*((m/(3*k))-(n/(2*G))),(1/3)*((m/(3*k))-(n/(2*G))),(1/3)*((m/(3*k))+(n/G)),0,0,0],
        [0,0,0,n/G,0,0],
        [0,0,0,0,n/G,0],
        [0,0,0,0,0,n/G]])

    def montaS(self, E, v):
        from mecanico.geometria_registry import GeometriaRegistry
        L = self.montaL(E, v)
        P = self.montaP(E, v)
        geometria = GeometriaRegistry.obter(self.geo)
        return geometria.calcular_S(E, v, P, L)

    def montaL(self, E, v):  # <------- FUNCIONANDO =======================
        c = E / ((1 + v) * (1 - 2 * v))
        x = np.array([[1 - v, v, v, 0, 0, 0],
                      [v, 1 - v, v, 0, 0, 0],
                      [v, v, 1 - v, 0, 0, 0],
                      [0, 0, 0, (1 - 2 * v) / 2, 0, 0],
                      [0, 0, 0, 0, (1 - 2 * v) / 2, 0],
                      [0, 0, 0, 0, 0, (1 - 2 * v) / 2]])
        L = c * x
        return L

    def montaP(self, E, v):  # <------- FUNCIONANDO =======================

        m = (1 + v) / (3 * (1 - v))
        n = (2 * (4 - 5 * v)) / (15 * (1 - v))
        k = E / (3 * (1 - 2 * v))
        G = E / (2 * (1 + v))

        self.P = np.array([[(1 / 3) * ((m / (3 * k)) + (n / G)), (1 / 3) * ((m / (3 * k)) - (n / (2 * G))),
                            (1 / 3) * ((m / (3 * k)) - (n / (2 * G))), 0, 0, 0],
                           [(1 / 3) * ((m / (3 * k)) - (n / (2 * G))), (1 / 3) * ((m / (3 * k)) + (n / G)),
                            (1 / 3) * ((m / (3 * k)) - (n / (2 * G))), 0, 0, 0],
                           [(1 / 3) * ((m / (3 * k)) - (n / (2 * G))), (1 / 3) * ((m / (3 * k)) - (n / (2 * G))),
                            (1 / 3) * ((m / (3 * k)) + (n / G)), 0, 0, 0],
                           [0, 0, 0, n / G, 0, 0],
                           [0, 0, 0, 0, n / G, 0],
                           [0, 0, 0, 0, 0, n / G]])
        return self.P

    def tensorS(self):
        from mecanico.geometria_registry import GeometriaRegistry
        geometria = GeometriaRegistry.obter(self.geo)
        self.S = geometria.calcular_S(self.E, self.v, self.P, self.L)
        return self.S


