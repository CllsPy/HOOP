from micmodelos import Micmodelos
import numpy as np


class Campbell(Micmodelos):
    def __init__(self):
        super().__init__()
        self.tipo = 'Campbell'
        self.fi = None
        self.K = None
        self.Ki = None
        self.Km = None
        self.kh = None
        self.K11 = None
        self.K22 = None
        self.K33 = None


    def calc(self, objH):

        if objH.analH.analise_type == 'condutividade':
            fi = objH.analH.fi
            Km = objH.matH[0].K
            Ki = objH.matH[1].K

            Ki = np.diag(Ki)

            M = 1 - fi ** (1 / 3)
            self.kh = Km * (2 * M - M ** 2) + (Km * Ki * (1 - M) ** 2) / (Ki * M + Km * (1 - M))

            self.fi = fi
            self.Km = Km
            self.Ki = Ki

            self.K11 = self.kh[0, 0]
            self.K22 = self.kh[1, 1]
            self.K33 = self.kh[2, 2]



