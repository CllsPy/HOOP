from micmodelos import Micmodelos


class Popovic(Micmodelos):
    def __init__(self):
        super().__init__()
        self.modelo = 'popovic'
        # Propriedades Mecânicas
        self.C = None  # tensor constitutivo homogeneizado
        self.Ci = None  # tensor constitutivo da inclusão
        self.Cm = None  # tensor constitutivo da matriz
        self.Eh = None  # módulo de elasticidade homogeneizado
        self.Ei = None  # módulo de elasticidade da inclusão
        self.Em = None  # módulo de elasticidade da matriz
        self.vi = None  # poisson da inclusão
        self.vm = None  # poisson da matriz
        self.vh = None  # poisson homogeneizado
        self.fi = None  # fração volumétrica da inclusão

        # Propriedades de Condutividade
        self.K = None  # tensor de condutividade homogeneizado
        self.Ki = None  # tensor de condutividade da inclusão
        self.Km = None  # tensor de condutividade da matriz
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
            Em = objH.matH[0].E
            vm = objH.matH[0].v
            Cm = objH.matH[0].L
            Ei = objH.matH[1].E
            vi = objH.matH[1].v
            Ci = objH.matH[1].L

            V = fi * Ci + (1 - fi) * Cm
            R = ((fi * (Ci ** -1)) + ((1 - fi) * (Cm ** -1))) ** -1
            C = (1 / 2) * (R + V)

            self.Eh = (-2 * C[0, 1] ** 2 + C[0, 1] * C[0, 0] + C[0, 0] ** 2) / (C[0, 1] + C[0, 0])
            objH.modH.vh = C[0, 1] / (C[0, 1] + C[0, 0])

            kh = objH.modH.Eh / (3 * (1 - 2 * objH.modH.vh))
            Gh = objH.modH.Eh / (2 * (1 + objH.modH.vh))
            objH.modH.kh = kh
            objH.modH.Gh = Gh

            objH.modH.C = C
            objH.modH.Ci = Ci
            objH.modH.Cm = Cm
            objH.modH.fi = fi
            objH.modH.Em = Em
            objH.modH.vm = vm
            objH.modH.Ei = Ei
            objH.modH.vi = vi

        elif objH.analH.analise_type == 'condutividade':
            fi = objH.analH.fi
            Km = objH.matH[0].K
            Ki = objH.matH[1].K

            V = fi * Ki + (1 - fi) * Km
            R = ((fi * (Ki ** -1)) + ((1 - fi) * (Km ** -1))) ** -1
            K = (1 / 2) * (R + V)

            self.kh = K
            self.fi = fi
            self.Km = Km
            self.Ki = Ki

            self.K11 = self.kh[0, 0]
            self.K22 = self.kh[1, 1]
            self.K33 = self.kh[2, 2]
