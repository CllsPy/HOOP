from micmodelos.micmodelos import Micmodelos

import numpy as np
from scipy.linalg import inv


class MoriTanaka(Micmodelos):
    def __init__(self):
        super().__init__()
        self.tipo = "Mori-Tanaka"
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
        self.Alpha = None
        self.Alphai = None
        self.Alpham = None
        self.kh = None
        self.Gh = None
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
        print(f"=== MoriTanaka.calc() chamado ===")
        print(f"analise_tipo: {objH.analise_tipo}")
        print(f"fi: {objH.fi}")
        print(f"Num materiais: {len(objH.materiais)}")

        if objH.material_tipo == 'mecanica':
            fi = objH.fi
            S = objH.materiais[0].S
            Em = objH.materiais[0].E
            vm = objH.materiais[0].v
            Cm = objH.materiais[0].L
            Ei = objH.materiais[1].E
            vi = objH.materiais[1].v
            Ci = objH.materiais[1].L
            I = np.eye(6)

            C = Cm @ (np.eye(Cm.shape[0]) + fi * (S - np.eye(Cm.shape[0])) @ inv(inv(Cm - Ci) @ Cm - S)) @ \
                inv(np.eye(Cm.shape[0]) + fi * S @ inv(inv(Cm - Ci) @ Cm - S))

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

        elif objH.analise_type == 'condutividade':
            fi = objH.fi
            Km = objH.materiais[0].K
            S = objH.materiais[0].S
            Ki = objH.materiais[1].K
            I = np.eye(3)


            kh = Km @ (np.eye(Km.shape[0]) +
                       fi * (S - np.eye(S.shape[0])) @ inv(((np.linalg.inv(Km - Ki) @ Km) - S))) \
                 @ inv(np.eye(Km.shape[0]) + fi * S @ inv(((np.linalg.inv(Km - Ki) @ Km) - S)))

            #self.fi = fi
            #self.Km = Km
            #self.Ki = Ki

            #termo1 = Km @ (I + fi * (S - I))
            #termo2 = np.linalg.inv((Km - Ki) @ Km - S)
            #numerador = termo1 @ termo2
            #denominador = (I + fi * S) @ termo2
            #self.kh = numerador / denominador

            self.kh = kh
            self.K11 = self.kh[0, 0]
            self.K22 = self.kh[1, 1]
            self.K33 = self.kh[2, 2]


        elif objH.analise_type == 'dosage':
            objH.mix = objH.mix.calc()

            S = objH.materiais[0].S
            Em = objH.materiais[0].E
            vm = objH.materiais[0].v
            Cm = objH.materiais[0].L
            Ei = objH.materiais[1].E
            vi = objH.materiais[1].v
            Ci = objH.materiais[1].L

            objH.materiais[0].E = objH.mix.fckmodels.Ec
            objH.materiais[0].v = 0.2055

            aux = objH.materiais[0].tensorL()
            C = aux.L

            I = np.eye(6)
            X = ((Cm - Ci) @ np.linalg.inv(Cm) - S)
            F = (C @ I - Cm @ I) @ np.linalg.inv(Cm @ (S - I) @ np.linalg.inv(X) - C @ S @ np.linalg.inv(X))
            mod.fi = np.trace(F) / 6

        elif analH_type == 'termomechanics':
            fi = objH.fi
            S = objH.materiais[0].S
            Em = objH.materiais[0].E
            vm = objH.materiais[0].v
            Cm = objH.materiais[0].L
            alpha_m = objH.materiais[0].Alpha

            Ei = objH.materiais[1].E
            vi = objH.materiais[1].v
            Ci = objH.materiais[1].L
            alpha_i = objH.materiais[1].Alpha

            I = np.eye(6)

            C = Cm @ (I + fi * (S - I) @ np.linalg.inv(((Cm - Ci) @ np.linalg.inv(Cm) - S))) @ np.linalg.inv(
                I + fi * S @ np.linalg.inv(((Cm - Ci) @ np.linalg.inv(Cm) - S)))

            mod.Eh = (-2 * C[0, 1] ** 2 + C[0, 1] * C[0, 0] + C[0, 0] ** 2) / (C[0, 1] + C[0, 0])
            mod.vh = C[0, 1] / (C[0, 1] + C[0, 0])

            Bm = objH.tensorB(1 - fi, Cm, Ci, C)
            Bi = objH.tensorB(fi, Ci, Cm, C)

            ai = fi * alpha_i * Bi
            am = (1 - fi) * alpha_m * Bm
            alpha = ai + am

            mod.C = C
            mod.Ci = Ci
            mod.Cm = Cm
            mod.fi = fi
            mod.Em = Em
            mod.vm = vm
            mod.Ei = Ei
            mod.vi = vi
            mod.Alpha = alpha
            mod.Alphai = ai
            mod.Alpham = am
