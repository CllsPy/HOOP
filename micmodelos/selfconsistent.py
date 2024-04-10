import numpy as np
from micmodelos import Micmodelos


class SelfConsistent(Micmodelos):
    def __init__(self):
        super().__init__()
        self.tol = 1e-8
        self.N3 = 10
        self.tipo = 'Auto-Consistente'
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
        # self.status = 'supported'
        # homo_analH_type = homo.analH['type']

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

            Co = Cm  # initial condition

            # tolerância
            tol = self.tol
            N3 = self.N3
            nite = 0

            while N3 > tol:

                C = Cm + fi * (Ci - Cm) @ np.linalg.inv(I - (S @ (np.linalg.inv(Co))) @ (Co - Ci))

                E = (-2 * C[2, 1] ** 2 + C[2, 1] * C[2, 2] + C[2, 2] ** 2) / (C[2, 1] + C[2, 2])
                v = C[2, 1] / (C[2, 1] + C[2, 2])

                S = objH.matH[0].montaS(E,v)

                N1 = E
                N2 = (-2 * Co[2, 1] ** 2 + Co[2, 1] * Co[2, 2] + Co[2, 2] ** 2) / (Co[2, 1] + Co[2, 2])
                N3 = (np.absolute(N1)-np.absolute(N2))/np.absolute(N2)

                #N1 = np.linalg.norm(C)
                #N2 = np.linalg.norm(Co)
                #N3 = np.sqrt(((N1 - N2) / N2) ** 2)
                # print(N3)

                Co = C
                nite += 1

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



        elif  objH.analH.analise_type == 'condutividade':
            fi = objH.analH.fi
            Km = objH.matH[0].K
            S = objH.matH[0].S
            Ki = objH.matH[1].K

            I = np.eye(3)
            Ko = Km  # initial condition

            tol = self.tol
            N3 = self.N3
            nite = 0

            while N3 > tol:
                K = (1 / 4) * ((3 * fi - 1) * Ki + (3 * (1 - fi) - 1) * Km + np.sqrt(
                    ((3 * fi - 1) * Ki + (3 * (1 - fi) - 1) * Km) ** 2 + 8 * Km * Ki))

                N1 = np.linalg.norm(K)
                N2 = np.linalg.norm(Ko)
                N3 = np.sqrt(((N1 - N2) / N2) ** 2)

                Ko = K
                nite += 1

            self.kh = K
            self.fi = fi
            self.Km = Km
            self.Ki = Ki

            self.K11 = self.kh[0, 0]
            self.K22 = self.kh[1, 1]
            self.K33 = self.kh[2, 2]



