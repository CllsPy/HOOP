from micmodelos import Micmodelos
import numpy as np

class DiluteSuspension(Micmodelos):
    def __init__(self):
        super().__init__()
        self.tipo = 'Dilute Suspension'
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
        self.K = None  # homogene tensor of conductivity
        self.Ki = None  # inclusion tensor of conductivity
        self.Km = None  # matrix tensor of conductivity
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
            S = objH.matH[0].S
            Em = objH.matH[0].E
            vm = objH.matH[0].v
            Cm = objH.matH[0].L
            Ei = objH.matH[1].E
            vi = objH.matH[1].v
            Ci = objH.matH[1].L

            I = np.eye(6)

            A = np.linalg.inv(I + np.dot(S, np.dot(np.linalg.inv(Cm), Ci - Cm)))
            C = Cm + fi * np.dot(Ci - Cm, A)

            self.Eh = (-2 * C[0, 1] ** 2 + C[0, 1] * C[0, 0] + C[0, 0] ** 2) / (C[0, 1] + C[0, 0])
            self.vh = C[0, 1] / (C[0, 1] + C[0, 0])

            self.C = C
            self.Ci = Ci
            self.Cm = Cm
            self.fi = fi
            self.Em = Em
            self.vm = vm
            self.Ei = Ei
            self.vi = vi

            #logging.debug(f"Este é o valor de {self.Eh}")

        elif objH.analH.analise_type == 'condutividade':
            fi = objH.analH.fi
            Km = objH.matH[0].K
            S = objH.matH[0].S
            Ki = objH.matH[1].K

            I = np.eye(3)
            A = np.linalg.inv(I + np.dot(S, np.dot(np.linalg.inv(Km), Ki - Km)))
            kh = Km + fi * np.dot(Ki - Km, A)

            self.kh = kh
            self.fi = fi
            self.Km = Km
            self.Ki = Ki

            self.K11 = self.kh[0, 0]
            self.K22 = self.kh[1, 1]
            self.K33 = self.kh[2, 2]
