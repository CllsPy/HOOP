from micmodelos import Micmodelos
import numpy as np


class Hamilton(Micmodelos):
    def __init__(self):
        super().__init__()
        self.n = 6
        self.tipo = 'Hamilton'
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
        self.K11 = None
        self.K22 = None
        self.K33 = None
        self.kh = None

    def set_parameters(self, Em, vm, Ei, vi, fi):
        self.Em = Em
        self.Ei = Ei
        self.vm = vm
        self.vi = vi
        self.fi = fi

    def calc(self, objH):
        if objH.analH.analise_type == 'mecanica':
            print('analH not supported')
            return

        elif objH.analH.analise_type == 'condutividade':
            fi = objH.analH.fi
            Km = objH.matH[0].K
            Ki = objH.matH[1].K
            n = self.n
            fm = 1 - fi

            alpha = n * Km[0, 0] / ((n - 1) * Km[0, 0] + Ki[0, 0])
            kh = (fm * Km[0, 0] + alpha * fi * Ki[0, 0]) / (fm + alpha * fi)

            aux = np.zeros((3, 3))
            aux[0, 0] = kh
            aux[1, 1] = kh
            aux[2, 2] = kh

            self.kh = aux
            self.fi = fi
            self.Km = Km
            self.Ki = Ki

            self.K11 = self.kh[0, 0]
            self.K22 = self.kh[1, 1]
            self.K33 = self.kh[2, 2]
