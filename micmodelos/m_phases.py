from micmodelos import Micmodelos
# from homogenizacao import Homogenizacao
import numpy as np


class MPhases(Micmodelos):
    def __init__(self):
        super().__init__()
        self.modelo = 'M-Fases'
        self.C = None
        self.Ci = None
        self.Cm = None
        self.Cr = None
        self.Eh = None
        self.Ei = None
        self.Em = None
        self.Er = None
        self.vi = None
        self.vm = None
        self.vr = None
        self.vh = None
        self.fi = None
        self.fm = None
        self.fr = None
        self.K = None
        self.Ki = None
        self.Km = None
        self.kh = None
        self.Gh = None

    @staticmethod
    def set(Em, vm, Ei, vi, Er, vr, fi, fm, fr):
        Em = None
        Ei = None
        Er = None
        vm = None
        vi = None
        vr = None
        fi = None
        fm = None
        fr = None

    def calc(self, objH):
        if objH.analH.tipo == 'mecanica':

            fi = objH.analH.fi  # fi = 0
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
            S = objH.matH[0].S

            Si = objH.matH[1].S
            Sr = objH.matH[2].S

            DS = Si - Sr
            I = np.eye(6)

            Ar = np.linalg.inv(Cr - Cm) @ Cm
            Ai = np.linalg.inv(Ci - Cm) @ Cm

            Phi_r = -np.linalg.inv(Sr + Ar + DS @ (Sr + Ar - (fr / fi) * DS) @ np.linalg.inv(Si + Ai - (fi / fi) * DS))
            Phi_i = -np.linalg.inv(DS + (Sr + Ar) @ np.linalg.inv(Sr + Ar - (fr / fi) * DS) @ (Si + Ai - (fi / fi) * DS))

            Ad_i = I + Si @ Phi_i + (fr / fi) * DS @ (Phi_r - Phi_i)
            Ad_r = I + Sr @ Phi_r + DS @ Phi_i

            Ag_r = Ad_r @ np.linalg.inv(fm * I + fi * Ad_i + fr * Ad_r)
            Ag_i = Ad_i @ np.linalg.inv(fm * I + fi * Ad_i + fr * Ad_r)

            C = Cm + fi * (Ci - Cm) @ Ag_i + fr * (Cr - Cm) @ Ag_r

            E = (-2 * C[0, 1] ** 2 + C[0, 1] * C[0, 0] + C[0, 0] ** 2) / (C[0, 1] + C[0, 0])
            v = C[0, 1] / (C[0, 1] + C[0, 0])

            self.Eh = E
            self.vh = v

            kh = self.Eh / (3 * (1 - 2 * self.vh))
            Gh = self.Eh / (2 * (1 + self.vh))

            self.kh = kh
            self.Gh = Gh
            self.C = C
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



