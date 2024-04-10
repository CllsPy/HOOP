import numpy as np
from micmodelos import Micmodelos

class Reuss(Micmodelos):
    def __init__(self):
        self.tipo = 'Reuss'
        # Mechanics properties
        self.C = None  # constitutive tensor
        self.Ci = None  # constitutive tensor of inclusion
        self.Cm = None  # constitutive tensor of matrix
        self.Eh = None  # homogene young modulus
        self.Ei = None  # inclusion young modulus
        self.Em = None  # matrix young modulus
        self.vi = None  # poisson inclusion
        self.vm = None  # poisson matrix
        self.vh = None  # poisson homogene
        self.fi = None  # fraction volumetric of inclusion
        # Conductivity properties
        self.K = None  # homogene tensor of conductivity
        self.Ki = None  # inclusion tensor of conductivity
        self.Km = None  # matrix tensor of conductivity
        self.kh = None  # modulo volumetrico
        self.Gh = None  # módulo cisalhante
        self.K11 = None
        self.K22 = None
        self.K33 = None

    def set(self, Em, vm, Ei, vi, fi):
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

            # Equação de recorrência para o modelo de Reuss (regra da mistura)
            self.C = np.linalg.inv(fi * np.linalg.inv(Ci) + (1 - fi) * np.linalg.inv(Cm))
            C = self.C
            # Calculando o módulo de elasticidade e coeficiente de poisson do compósito
            self.Eh = (-2 * C[0, 1] ** 2 + C[0, 1] * C[0, 0] + C[0, 0] ** 2) / (C[0, 1] + C[0, 0])
            self.vh = C[0, 1] / (C[0, 1] + C[0, 0])

            kh = self.Eh / (3 * (1 - 2 * self.vh))
            Gh = self.Eh / (2 * (1 + self.vh))
            self.kh = kh
            self.Gh = Gh

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

            self.kh = np.linalg.inv(fi * np.linalg.inv(Ki) + (1 - fi) * np.linalg.inv(Km))

            self.fi = fi
            self.Km = Km
            self.Ki = Ki

            self.K11 = self.kh[0, 0]
            self.K22 = self.kh[1, 1]
            self.K33 = self.kh[2, 2]
