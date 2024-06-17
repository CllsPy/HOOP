from micmodelos import Micmodelos
from analise import Analise
import numpy as np


class Hashin_Sup(Micmodelos):
    def __init__(self):
        super().__init__()
        self.tipo = "Hashin - Superior"
        self.C = None   # Tensor Constitutivo Homogeneizado
        self.Ci = None  # Tensor Constitutivo das Inclusões
        self.Cm = None  # Tensor Constitutivo da Matriz
        self.Eh = None  # Módulo de Elasticidade Homogneizado
        self.Ei = None  # Módulo de Elasticidade das Inclusões
        self.Em = None  # Módulo de Elasticidade da Matriz
        self.vi = None  # Coeficiente de Poison da Inclusão
        self.vm = None  # Coeficiente de Poison da Matriz
        self.vh = None  # Coeficiente de Poison Homogeneizado
        self.kh = None  # Módulo Volumétrico Homogeneizado
        self.Gh = None  # Módulo Cisalhante Homogeneizado
        self.fi = None  # Fração Volumétrica das Inclusões
        self.K = None   # Tensor Condutividade Térmica Homogeneizado
        self.Ki = None  # Condutividade Térmica das Inclusões
        self.Km = None  # Condutividade Térmica da Matriz
        self.K11 = None
        self.K22 = None
        self.K33 = None

    def set(self, Em, vm, Ei, vi, fi): #<------- FUNCIONANDO =======================
        self.Em = Em
        self.Ei = Ei
        self.vm = vm
        self.vi = vi
        self.fi = fi

    def calc(self, objH):  # <------- FUNCIONANDO =======================
        if objH.analH.analise_type == "mecanica":
            fi = objH.analH.fi
            Em = objH.matH[0].E
            vm = objH.matH[0].v
            Cm = objH.matH[0].L
            Ei = objH.matH[1].E
            vi = objH.matH[1].v
            Ci = objH.matH[1].L

            Km = Em / (3 * (1 - 2 * vm))
            Ki = Ei / (3 * (1 - 2 * vi))
            Gm = Em / (2 * (1 + vm))
            Gi = Ei / (2 * (1 + vi))

            if (Km>Ki and Gm>Gi):
                Ko = Km + fi / (1 / (Ki - Km) + 3 * (1 - fi) / (3 * Km + 4 * Gm))
                Kf = Ki + (1 - fi) / (1 / (Km - Ki) + 3 * fi / (3 * Ki + 4 * Gi))
                Go = Gm + fi / (1 / (Gi - Gm) + 6 * (1 - fi) * (Km + 2 * Gm) / (5 * Gm * (3 * Km + 4 * Gm)))
                Gf = Gi + (1 - fi) / (1 / (Gm - Gi) + 6 * fi * (Ki + 2 * Gi) / (5 * Gi * (3 * Ki + 4 * Gi)))
            else:
                Kf = Km + fi / (1 / (Ki - Km) + 3 * (1 - fi) / (3 * Km + 4 * Gm))
                Ko = Ki + (1 - fi) / (1 / (Km - Ki) + 3 * fi / (3 * Ki + 4 * Gi))
                Gf = Gm + fi / (1 / (Gi - Gm) + 6 * (1 - fi) * (Km + 2 * Gm) / (5 * Gm * (3 * Km + 4 * Gm)))
                Go = Gi + (1 - fi) / (1 / (Gm - Gi) + 6 * fi * (Ki + 2 * Gi) / (5 * Gi * (3 * Ki + 4 * Gi)))


            self.Eh = 9 * Ko * Go / (3 * Ko + Go)
            Ef = 9 * Kf * Gf / (3 * Kf + Gf)
            self.vh = (3 * Ko - 2 * Go) / (2 * (3 * Ko + Go))
            vf = (3 * Kf - 2 * Gf) / (2 * (3 * Kf + Gf))

            C = objH.matH[0].tensor_L(self.Eh, self.vh)

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

        elif  objH.analH.analise_type == 'condutividade': #<------- FALTA TESTAR =======================
            fi = objH.analH.fi
            Km = objH.matH[0].K
            S = objH.matH[0].S
            Ki = objH.matH[1].K
            I = np.eye(3)
            fm = 1 - fi

            kh = (Km.dot(Ki) + 2 * Ki.dot(Km * fm + Ki * fi)) / (2 * Ki + Ki * fm + Km * fi)



            self.kh = kh
            self.K11 = self.kh[0, 0]
            self.K22 = self.kh[1, 1]
            self.K33 = self.kh[2, 2]

        elif objH.analH.tipo == 'dosagem':
            print('Não suportado')

