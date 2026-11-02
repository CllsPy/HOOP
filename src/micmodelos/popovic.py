import numpy as np
from micmodelos.micmodelos import Micmodelos


class Popovic(Micmodelos):
    def __init__(self):
        super().__init__()
        self.tipo = 'popovic'
        # Propriedades Mecânicas
        self.C = None  # tensor constitutivo homogeneizado
        self.Ci = None  # tensor constitutivo da inclusão
        self.Cm = None  # tensor constitutivo da matriz
        self.Eh = None  # módulo de elasticidade homogeneizado
        self.Ei = None  # módulo de elasticidade da inclusão
        self.Em = None  # módulo de elasticidade da matriz
        self.vi = None  # poisson da inclusão
        self.vm = None  # poisson da matriz
        self.vh = None  # poisson homogeneizado
        self.fi = None  # fração volumétrica da inclusão

        # Propriedades de Condutividade
        self.K = None  # tensor de condutividade homogeneizado
        self.Ki = None  # tensor de condutividade da inclusão
        self.Km = None  # tensor de condutividade da matriz
        self.kh = None  # modulo volumetrico
        self.Gh = None  # módulo cisalhante

        self.K11 = None
        self.K22 = None
        self.K33 = None

    def set_properties(self, Em, vm, Ei, vi, fi):
        self.Em = Em
        self.Ei = Ei
        self.vm = vm
        self.vi = vi
        self.fi = fi

    def calc(self, objH):
        if objH.analH.analise_type == 'mecanica':
            fi = objH.analH.fi
            Em = objH.matH[0].E
            vm = objH.matH[0].v
            Cm = objH.matH[0].L
            Ei = objH.matH[1].E
            vi = objH.matH[1].v
            Ci = objH.matH[1].L

            V = fi * Ci + (1 - fi) * Cm
            R = np.linalg.inv(fi * np.linalg.inv(Ci) + (1 - fi) * np.linalg.inv(Cm))
            C = (1 / 2) * (R + V)

            self.Eh = (-2 * C[0, 1] ** 2 + C[0, 1] * C[0, 0] + C[0, 0] ** 2) / (C[0, 1] + C[0, 0])
            self.vh = C[0, 1] / (C[0, 1] + C[0, 0])

            self.kh = self.Eh / (3 * (1 - 2 * self.vh))
            self.Gh = self.Eh / (2 * (1 + self.vh))

            self.C = C
            self.Ci = Ci
            self.Cm = Cm
            self.fi = fi
            self.Em = Em
            self.vm = vm
            self.Ei = Ei
            self.vi = vi

        elif objH.analH.analise_type == 'condutividade':
            fi = objH.analH.fi
            Km = objH.matH[0].K
            Ki = objH.matH[1].K

            V = fi * Ki + (1 - fi) * Km
            R = np.linalg.inv(fi * np.linalg.inv(Ki) + (1 - fi) * np.linalg.inv(Km))
            K = (1 / 2) * (R + V)

            self.kh = K
            self.fi = fi
            self.Km = Km
            self.Ki = Ki

            self.K11 = self.kh[0, 0]
            self.K22 = self.kh[1, 1]
            self.K33 = self.kh[2, 2]
