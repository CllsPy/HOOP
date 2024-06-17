from fckmodels import FckModels
class NBR(FckModels):
    def __init__(self):
        super().__init__()
        self.fck = 0  # modelo de Andreassen: porcentagem passante
        self.a = None
        self.tipo = 'nbr'

    def calc(self, pck):
        fck = self.fck * 1e6
        a = self.a
        if 20 < self.fck <= 50:
            Ec = 1e3 * a * 5600 * self.fck ** 0.5
        elif 50 < self.fck <= 90:
            Ec = 1e3 * 21.5 * 1e3 * ((self.fck / 10 * 1.25) ** (1 / 3))
        else:
            print('Análise não suportada')
            return
        self.Ec = Ec
