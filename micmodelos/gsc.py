import numpy as np
from micmodelos import Micmodelos


class GSC(Micmodelos):
    def __init__(self):
        super().__init__()
        self.tipo = 'GSC'
        self.C = None
        self.Ci = None
        self.Cm = None
        self.Eh = None
        self.Ei = None
        self.Em = None
        self.vi = None
        self.vm = None
        self.vh = None
        self.fi = None
        self.K = None
        self.Ki = None
        self.Km = None
        self.kh = None
        self.Gh = None
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

            I = np.eye(6)

            Ki = Ei / (3 * (1 - 2 * vi))
            Gi = Ei / (2 * (1 + vi))
            Km = Em / (3 * (1 - 2 * vm))
            Gm = Em / (2 * (1 + vm))

            n1 = (Gi / Gm - 1) * (49 - 50 * vi * vm) + 35 * (Gi / Gm) * (vi - 2 * vm) + 35 * (2 * vi - vm)
            n2 = 5 * vi * (Gi / Gm - 8) + 7 * (Gi / Gm + 4)
            n3 = (Gi / Gm) * (8 - 10 * vm) + (7 - 5 * vm)

            A = 8 * (Gi / Gm - 1) * (4 - 5 * vm) * n1 * (fi ** (10 / 3)) - 2 * (
                        63 * (Gi / Gm - 1) * n2 + 2 * n1 * n3) * (fi ** (7 / 3)) + \
                252 * (Gi / Gm - 1) * n2 * (fi ** (5 / 3)) - 50 * (Gi / Gm - 1) * (7 - 12 * vm + 8 * vm ** 2) * n2 * fi + \
                4 * (7 - 10 * vm) * n2 * n3

            B = -2 * (Gi / Gm - 1) * (1 - 5 * vm) * n1 * (fi ** (10 / 3)) + 2 * (
                        63 * (Gi / Gm - 1) * n2 + 2 * n1 * n3) * (fi ** (7 / 3)) - \
                252 * (Gi / Gm - 1) * n2 * (fi ** (5 / 3)) + 75 * (Gi / Gm - 1) * (3 - vm) * vm * n2 * fi + \
                1.5 * (15 * vm - 7) * n2 * n3

            D = 4 * (Gi / Gm - 1) * (5 * vm - 7) * n1 * (fi ** (10 / 3)) - 2 * (
                        63 * (Gi / Gm - 1) * n2 + 2 * n1 * n3) * (fi ** (7 / 3)) + \
                252 * (Gi / Gm - 1) * n2 * (fi ** (5 / 3)) + 25 * (Gi / Gm - 1) * (vm ** 2 - 7) * n2 * fi - \
                (7 + 5 * vm) * n2 * n3

            K = (Km + fi * (Ki - Km) * (3 * Km + 4 * Gm) / (3 * Km + 4 * Gm + 3 * (1 - fi) * (Ki - Km)))

            delta = (2 * B / Gm) ** 2 - 4 * (A * D / Gm ** 2)
            if delta > 0:
                G = (-(2 * B / Gm) + np.sqrt(delta)) / (2 * (A / Gm ** 2))
            elif delta == 0:
                G = -(2 * B / Gm) / (2 * (A / Gm ** 2))

            E = 9 * K * G / (G + 3 * K)
            self.Eh = E
            v = (3 * K - 2 * G) / (2 * (G + 3 * K))
            self.vh = v

            c = E / ((1 + v) * (1 - 2 * v))
            self.C = c * np.array([[1 - v, v, v, 0, 0, 0],
                                   [v, 1 - v, v, 0, 0, 0],
                                   [v, v, 1 - v, 0, 0, 0],
                                   [0, 0, 0, (1 - 2 * v) / 2, 0, 0],
                                   [0, 0, 0, 0, (1 - 2 * v) / 2, 0],
                                   [0, 0, 0, 0, 0, (1 - 2 * v) / 2]])

            self.kh = K
            self.Gh = G
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
            Ki = objH.matH[1].K

            self.kh = (1 / 4) * ((3 * fi - 1) * Ki + (3 * (1 - fi) - 1) * Km + np.sqrt(
                ((3 * fi - 1) * Ki + (3 * (1 - fi) - 1) * Km) ** 2 + 8 * Km * Ki))

            self.fi = fi
            self.Km = Km
            self.Ki = Ki

            self.K11 = self.kh[0, 0]
            self.K22 = self.kh[1, 1]
            self.K33 = self.kh[2, 2]

