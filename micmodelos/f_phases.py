
from micmodelos import Micmodelos
import numpy as np


class FPhases(Micmodelos):
    def __init__(self):
        super().__init__()
        self.modelo = 'F-Fases'
        self.C = None  # tensor constitutivo homogeneizado
        self.Ci = None  # tensor constitutivo da inclusão
        self.Cm = None  # tensor constitutivo da matriz
        self.Cr = None  # tensor constitutivo do revestimento
        self.Eh = None  # módulo de elasticidade homogeneizado
        self.Ei = None  # módulo de elasticidade da inclusão
        self.Em = None  # módulo de elasticidade da matriz
        self.Er = None  # módulo de elasticidade do revestimento
        self.vi = None  # poisson da inclusão
        self.vm = None  # poisson da matriz
        self.vr = None  # poisson do revestimento
        self.vh = None  # poisson homogeneizado
        self.fi = None  # fração volumétrica da inclusão
        self.fm = None  # fração volumétrica da matriz
        self.fr = None  # fração volumétrica do revestimento

        # Propriedades de Condutividade
        self.K = None  # tensor de condutividade homogeneizado
        self.Ki = None  # tensor de condutividade da inclusão
        self.Km = None  # tensor de condutividade da matriz
        self.kh = None  # modulo volumetrico
        self.Gh = None  # módulo cisalhante

    @staticmethod
    def set(Em, vm, Ei, vi, fi):
        self.Em = Em
        self.Ei = Ei
        self.Er = Er
        self.vm = vm
        self.vi = vi
        self.vr = vr
        self.fi = fi
        self.fm = fm
        self.fr = fr

    def calc(self, objH):
        if objH.analH.analise_type == 'mecanica':
            fi = objH.analH.fi
            fm = objH.analH.fm
            fr = objH.analH.fr
            Em = objH.matH[0].E
            vm = objH.matH[0].v
            Cm = objH.matH[0].L
            Ei = objH.matH[1].E
            vi = objH.matH[1].v
            Ci = objH.matH[1].L
            Er = objH.matH[2].E
            vr = objH.matH[2].v
            Cr = objH.matH[2].L


            # Corrigindo as frações volumétricas da inclusão e revestimento para
            # aplicação do modelo auto-consistente generalizado
            #fic = fi / (fi + fr)
            #frc = fr / (fi + fr)
            #fo = fi + fr
            #fm = 1 - fo

            # Homogeneizando revestimento e inclusão
            Eh, vh = self.GSCM(Er, vr, Ei, vi, fi)
            fo = fi + fr
            # Homogeneizando a matriz com a nova inclusão
            E, v = self.GSCM(Em, vm, Eh, vh, fo)

            self.Eh = E
            self.vh = v

            kh = self.Eh / (3 * (1 - 2 * self.vh))
            Gh = self.Eh / (2 * (1 + self.vh))
            self.kh = kh
            self.Gh = Gh

            self.C = Cm
            self.Ci = Ci
            self.Cm = Cm
            self.Cr = Cr
            self.fi = fi
            self.fm = fm
            self.fr = fr
            self.Em = Em
            self.vm = vm
            self.Ei = Ei
            self.vi = vi
            self.Er = Er
            self.vr = vr

        elif objH.analH.tipo == 'condutividade':
            print('Não suporta!')

    def GSCM(self, Em, vm, Ei, vi, fi):
        # módulo de elasticidade volumétrico:
        Ki = Ei / (3 * (1 - 2 * vi))
        # módulo de elasticidade ao cisalhamento:
        Gi = Ei / (2 * (1 + vi))
        # módulo de elasticidade volumétrico:
        Km = Em / (3 * (1 - 2 * vm))
        # módulo de elasticidade ao cisalhamento:
        Gm = Em / (2 * (1 + vm))

        # Parâmetros auxiliares
        n1 = (Gi / Gm - 1) * (49 - 50 * vi * vm) + 35 * (Gi / Gm) * (vi - 2 * vm) + 35 * (2 * vi - vm)
        n2 = 5 * vi * (Gi / Gm - 8) + 7 * (Gi / Gm + 4)
        n3 = (Gi / Gm) * (8 - 10 * vm) + (7 - 5 * vm)
        # Geometria da Inclusão

        # Calculando os parâmetros A, B e D da Equação do segundo grau de
        # Christensen e Lo.

        A = 8 * (Gi / Gm - 1) * (4 - 5 * vm) * n1 * (fi ** (10 / 3)) - 2 * (
                63 * (Gi / Gm - 1) * n2 + 2 * n1 * n3) * (fi ** (7 / 3)) + \
            252 * (Gi / Gm - 1) * n2 * (fi ** (5 / 3)) - 50 * (Gi / Gm - 1) * (7 - 12 * vm + 8 * vm ** 2) * n2 * fi + \
            4 * (7 - 10 * vm) * n2 * n3

        B = -2 * (Gi / Gm - 1) * (1 - 5 * vm) * n1 * (fi ** (10 / 3)) + \
            2 * (63 * (Gi / Gm - 1) * n2 + 2 * n1 * n3) * (fi ** (7 / 3)) - \
            252 * (Gi / Gm - 1) * n2 * (fi ** (5 / 3)) + \
            75 * (Gi / Gm - 1) * (3 - vm) * vm * n2 * fi + \
            1.5 * (15 * vm - 7) * n2 * n3

        D = 4 * (Gi / Gm - 1) * (5 * vm - 7) * n1 * (fi ** (10 / 3)) - 2 * (
                63 * (Gi / Gm - 1) * n2 + 2 * n1 * n3) * (fi ** (7 / 3)) + \
            252 * (Gi / Gm - 1) * n2 * (fi ** (5 / 3)) + 25 * (Gi / Gm - 1) * (vm ** 2 - 7) * n2 * fi - \
            (7 + 5 * vm) * n2 * n3

        # Equação a ser resolvida
        # módulo de elasticidade volumétrico efetivo:
        K = (Km + fi * (Ki - Km) * (3 * Km + 4 * Gm) / (3 * Km + 4 * Gm + 3 * (1 - fi) * (Ki - Km)))

        # A[G / Gm]² + 2B[G / Gm] + D = 0
        delta = (2 * B / Gm) ** 2 - 4 * (A * D / Gm ** 2)
        if delta > 0:
            G = (-(2 * B / Gm) + np.sqrt(delta)) / (2 * (A / Gm ** 2))
        elif delta == 0:
            G = -(2 * B / Gm) / (2 * (A / Gm ** 2))

        # Retornando para Módulo de Elasticidade e Poisson
        # módulo de elasticidade longitudinal efetivo:
        E = 9 * K * G / (G + 3 * K)
        # coeficiente de Poisson efetivo:
        v = (3 * K - 2 * G) / (2 * (G + 3 * K))

        return E, v
