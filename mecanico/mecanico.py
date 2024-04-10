from materiais import Materiais
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
        if self.geo == 'esfera':
            P = self.montaP(E,v)
            L = self.montaL(E,v)
            S = np.dot(P, L)
            return S

        elif self.geo == 'cilindro': #<------- FALTA TESTAR =======================
            S = np.zeros((6, 6))
            k = 0.03 / 100
            v = self.v
            S[0, 0] = ((2.0 - v) / (1.0 - v)) * (k ** 2) * (math.log(2.0 / k) - ((5.0 - 2.0 * v) / (4.0 - 2.0 * v)))
            S[0, 1] = -((1.0 - 2.0 * v) / (2.0 - 2.0 * v)) * (k ** 2) * (
                        math.log(2.0 / k) - ((3.0 - 4.0 * v) / (2.0 - 4.0 * v)))
            S[0, 2] = S[0, 1]
            S[1, 0] = ((v) / (2.0 - 2.0 * v)) - ((1.0 + v) / (2.0 - 2.0 * v)) * (k ** 2) * (
                        math.log(2.0 / k) - ((3.0 + 2.0 * v) / (2.0 + 2.0 * v)))
            S[1, 1] = ((5.0 - 4.0 * v) / (8.0 - 8.0 * v)) - ((1.0 - 2.0 * v) / (4.0 - 4.0 * v)) * (k ** 2) * (
                        math.log(2.0 / k) - ((1.0 - 8.0 * v) / (4.0 - 8.0 * v)))
            S[1, 2] = -((1.0 - 4.0 * v) / (8.0 - 8.0 * v)) - ((1.0 - 2.0 * v) / (4.0 - 4.0 * v)) * (k ** 2) * (
                        math.log(2.0 / k) - ((5.0 - 8.0 * v) / (4.0 - 8.0 * v)))
            S[2, 0] = S[1, 0]
            S[2, 1] = S[1, 2]
            S[2, 2] = S[1, 1]
            S[3, 3] = (3.0 - 4.0 * v) / (2 * (4.0 - 4.0 * v))
            S[4, 4] = 1.0 / 4.0
            S[5, 5] = 1.0 / 4.0
            return S

        elif self.geo == 'disco': #<------- FALTA TESTAR =======================
            S = np.zeros((6, 6))
            E = self.E
            v = self.v
            c0 = E * (1 - v) / (1 - v - 2 * v * v)
            c1 = E * v / (1 - v - 2 * v * v)

            S[2, 0] = c1 / c0
            S[3, 3] = 0.5
            S[2, 1] = c1 / c0
            S[4, 4] = 0.5
            S[2, 2] = 1.0

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

    def tensorS(self): #<------- FUNCIONANDO =======================
        if self.geo == 'esfera':
            self.S = np.dot(self.P, self.L)
            return self.S
        elif self.geo == 'cilindro': #<------- FALTA TESTAR =======================
            S = np.zeros((6, 6))
            k = 0.03 / 100
            v = self.v
            S[0, 0] = ((2.0 - v) / (1.0 - v)) * (k ** 2) * (math.log(2.0 / k) - ((5.0 - 2.0 * v) / (4.0 - 2.0 * v)))
            S[0, 1] = -((1.0 - 2.0 * v) / (2.0 - 2.0 * v)) * (k ** 2) * (
                        math.log(2.0 / k) - ((3.0 - 4.0 * v) / (2.0 - 4.0 * v)))
            S[0, 2] = S[0, 1]
            S[1, 0] = ((v) / (2.0 - 2.0 * v)) - ((1.0 + v) / (2.0 - 2.0 * v)) * (k ** 2) * (
                        math.log(2.0 / k) - ((3.0 + 2.0 * v) / (2.0 + 2.0 * v)))
            S[1, 1] = ((5.0 - 4.0 * v) / (8.0 - 8.0 * v)) - ((1.0 - 2.0 * v) / (4.0 - 4.0 * v)) * (k ** 2) * (
                        math.log(2.0 / k) - ((1.0 - 8.0 * v) / (4.0 - 8.0 * v)))
            S[1, 2] = -((1.0 - 4.0 * v) / (8.0 - 8.0 * v)) - ((1.0 - 2.0 * v) / (4.0 - 4.0 * v)) * (k ** 2) * (
                        math.log(2.0 / k) - ((5.0 - 8.0 * v) / (4.0 - 8.0 * v)))
            S[2, 0] = S[1, 0]
            S[2, 1] = S[1, 2]
            S[2, 2] = S[1, 1]
            S[3, 3] = (3.0 - 4.0 * v) / (2 * (4.0 - 4.0 * v))
            S[4, 4] = 1.0 / 4.0
            S[5, 5] = 1.0 / 4.0

            #self.S = S
            #return S

        elif self.geo == 'disco': #<------- FALTA TESTAR =======================
            S = np.zeros((6, 6))
            E = self.E
            v = self.v
            c0 = E * (1 - v) / (1 - v - 2 * v * v)
            c1 = E * v / (1 - v - 2 * v * v)

            S[2, 0] = c1 / c0
            S[3, 3] = 0.5
            S[2, 1] = c1 / c0
            S[4, 4] = 0.5
            S[2, 2] = 1.0

            #self.S = S # SE QUISER RETORNO


