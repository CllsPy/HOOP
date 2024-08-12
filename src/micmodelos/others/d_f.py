from micmodelos import Micmodelos
import numpy as np


class DifferentialScheme(Micmodelos):
    def __init__(self):
        super().__init__()
        self.tipo = 'differential_scheme'
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
        self.kh = None  # modulo volumetrico
        self.Gh = None  # módulo cisalhante
        self.dfi = 0.01
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
            S = objH.matH[0].S
            Em = objH.matH[0].E
            vm = objH.matH[0].v
            Cm = objH.matH[0].L
            Ei = objH.matH[1].E
            vi = objH.matH[1].v
            Ci = objH.matH[1].L
            dfi = self.dfi
            Co = Cm
            I = np.eye(6)

            for i in (0, fi, dfi):
                C = Co
                E = (-2 * C[0, 1] ** 2 + C[0, 1] * C[0, 0] + C[0, 0] ** 2) / (C[0, 1] + C[0, 0])
                v = C[0, 1] / (C[0, 1] + C[0, 0])
                Ai = np.linalg.inv(I - np.dot(S, np.dot(np.linalg.inv(Co), (Co - Ci))))
                dC = (dfi / (1 - i)) * (Ci - Co) @ Ai

                objH.matH[0].E = E
                objH.matH[0].v = v
                aux = objH.matH[0].tensorS()
                S = aux

                Co = Co + dC
                #nite += 1

                self.Eh = E
                self.vh = v
                kh = self.Eh / (3 * (1 - 2 * self.vh))
                Gh = self.Eh / (2 * (1 + self.vh))
                self.kh = kh
                self.Gh = Gh
                self.C = objH.matH[0].L
                self.Ci = Ci
                self.Cm = Cm
                self.fi = fi
                self.Em = Em
                self.vm = vm
                self.Ei = Ei
                self.vi = vi

        elif objH.analH.analise_type == 'condutividade':
            print('Não suportado!')


