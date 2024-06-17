from fckmodels import FckModels
class Generic(FckModels):
    def __init__(self):
        super().__init__()
        self.fck = 0  # modelo de Andreassen: porcentagem passante
        self.tipo = 'generic'
        self.Ec = 35e9
        self.vc = 0.20

    def calc(self, pck):
        pass

    def set_ev(self, E, v):
        self.Ec = E
        self.vc = v
