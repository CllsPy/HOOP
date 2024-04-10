import numpy as np
from micmodelos import Micmodelos


class Voigt(Micmodelos):
    def __init__(self):
        super().__init__()  # Iniciar atributos de Mic
        self.tipo = 'Voigt'
        self.C = None   # Tensor Constitutivo Homogeneizado
        self.Ci = None  # Tensor Constitutivo das Inclusões
        self.Cm = None  # Tensor Constitutivo da Matriz
        self.Eh = None  # Módulo de Elasticidade Homogneizado
        self.Ei = None  # Módulo de Elasticidade das Inclusões
        self.Em = None  # Módulo de Elasticidade da Matriz
        self.vi = None  # Coeficiente de Poison da Inclusão
        self.vm = None  # Coeficiente de Poison da Matriz
        self.vh = None  # Coeficiente de Poison Homogeneizado
        self.kh = None  # Módulo Volumétrico Homogeneizado
        self.Gh = None  # Módulo Cisalhante Homogeneizado
        self.fi = None  # Fração Volumétrica das Inclusões
        self.K = None   # Tensor Condutividade Térmica Homogeneizado
        self.Ki = None  # Condutividade Térmica das Inclusões
        self.Km = None  # Condutividade Térmica da Matriz
        self.K11 = None
        self.K22 = None
        self.K33 = None

    def set(self, Em, vm, Ei, vi, fi):  # <------- FUNCIONANDO =======================
        self.Em = Em
        self.Ei = Ei
        self.vm = vm
        self.vi = vi
        self.fi = fi

    def calc(self, objH):  # <------- FUNCIONANDO =======================
        if objH.analH.analise_type == 'mecanica':
            fi = objH.analH.fi
            Em = objH.matH[0].E
            vm = objH.matH[0].v
            Cm = objH.matH[0].L
            Ei = objH.matH[1].E
            vi = objH.matH[1].v
            Ci = objH.matH[1].L
            C = fi * Ci + (1 - fi) * Cm

            self.Eh = (-2 * C[0, 1] ** 2 + C[0, 1] * C[0, 0] + C[0, 0] ** 2) / (C[0, 1] + C[0, 0])
            self.vh = C[0, 1] / (C[0, 1] + C[0, 0])

            kh = self.Eh / (3 * (1 - 2 * self.vh))
            Gh = self.Eh / (2 * (1 + self.vh))

            self.kh = kh
            self.Gh = Gh
            self.C = C
            self.Ci = Ci
            self.Cm = Cm
            self.fi = fi
            self.Em = Em
            self.vm = vm
            self.Ei = Ei
            self.vi = vi

        elif  objH.analH.analise_type == 'condutividade': #<------- FALTA TESTAR =======================
            fi = objH.analH.fi
            Km = objH.matH[0].K
            Ki = objH.matH[1].K

            self.kh = fi * Ki + (1 - fi) * Km

            self.K11 = self.kh[0,0]
            self.K22 =  self.kh[1,1]
            self.K33 = self.kh[2,2]

        elif objH.analH.tipo == 'dosagem':
            Em = objH.matH[0].E
            vm = objH.matH[0].v
            Cm = objH.matH[0].L
            Ei = objH.matH[1].E
            vi = objH.matH[1].v
            Ci = objH.materiais[1].L

            objH.matH[0].E = objH.Mix.fckmodels.Ec
            objH.matH[0].v = 0.2055
            aux = objH.matH[0].tensorL()

            C = aux.L

            F = (C - Cm) * (Ci - Cm) ** (-1)
            self.fi = np.trace(F) / 6
