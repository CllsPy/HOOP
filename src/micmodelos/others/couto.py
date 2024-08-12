from micmodelos import Micmodelos
import numpy as np
import math


class Counto(Micmodelos):
    def __init__(self):
        super().__init__()
        self.tipo = 'Counto'
        self.C = None  # tensor constitutivo homogeneizado
        self.Ci = None  # tensor constitutivo da inclusão
        self.Cm = None  # tensor constitutivo da matriz
        self.Eh = None  # módulo de elasticidade homogeneizado
        self.Ei = None  # módulo de elasticidade da inclusão
        self.Em = None  # módulo de elasticidade da matriz
        self.vi = None  # coeficiente de poisson da inclusão
        self.vm = None  # coeficiente de poisson da matriz
        self.vh = None  # coeficiente de poisson homogeneizado
        self.fi = None  # fração volumétrica da inclusão
        self.kh = None  # modulo volumetrico
        self.Gh = None  # módulo cisalhante

    def set_properties(self, Em, vm, Ei, vi, fi):
        self.Em = Em
        self.Ei = Ei
        self.vm = vm
        self.vi = vi
        self.fi = fi

    def calc(self, objH):
        if objH.analH.analise_type == 'mecanica':
            fi = objH.analH.fi
            S = objH.matH[0].S
            Em = objH.matH[0].E
            vm = objH.matH[0].v
            Cm = objH.matH[0].L
            Ei = objH.matH[1].E
            vi = objH.matH[1].v
            Ci = objH.matH[1].L

            I = np.eye(6)

            C = Cm * (Cm * np.sqrt(fi) - Ci * np.sqrt(fi) - Cm) / (Cm * np.sqrt(fi) - Cm * fi - Ci * np.sqrt(fi) + Ci * fi - Cm)

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
            print('analH not supported')
