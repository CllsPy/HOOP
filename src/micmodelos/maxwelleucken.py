from micmodelos import Micmodelos
import numpy as np

class MaxwellEucken(Micmodelos):
    def __init__(self):
        self.tipo = 'Maxwelleucken'
        self.fi = None  # fração volumétrica da inclusão
        self.K = None  # tensor de condutividade homogeneizado
        self.Ki = None  # tensor de condutividade da inclusão
        self.Km = None  # tensor de condutividade da matriz
        self.kh = None
        self.K11 = None
        self.K22 = None
        self.K33 = None

    def calc(self, objH):
        if objH.analH.analise_type == 'condutividade':
            fi = objH.analH.fi
            Km = objH.matH[0].K
            Ki = objH.matH[1].K

            self.kh = Km * ((2 * Km + Ki - 2 * (Km - Ki) * fi) / (2 * Km + Ki + (Km - Ki) * fi))
            self.fi = fi
            self.Km = Km
            self.Ki = Ki

            self.K11 = self.kh[0, 0]
            self.K22 = self.kh[1, 1]
            self.K33 = self.kh[2, 2]
