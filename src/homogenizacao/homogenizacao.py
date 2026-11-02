from analise.analise import Analise
from micmodelos.micmodelos import Micmodelos
from mecanico.mecanico import Mecanico
import matplotlib.pyplot as plt

class Homogenizacao (object):
    def __init__(self):
        self.analH = Analise('mecanica', 'esfera', 0, 0, None)
        self.modH = Micmodelos
        self.matH = []
        self.tipo = None
        self.geo = None
        self.fi = 0
        self.fm = 0
        self.fr = None
        self.analise_tipo = None

    def calc(self):
        if self.tipo == 'global':    # <------- FUNCIONANDO =======================
            self.calcB()

        elif self.tipo == 'local':
            pass

    def calcB(self):
        from homogenizacao.calculadora_fracoes import CalculadoraFracoes
        CalculadoraFracoes.distribuir(self.analH, self.matH)

        for i, mat in enumerate(self.matH):
            mat.id = i
            mat.geo = self.analH.geo
            mat.calc()

        self.modH.calc(self)

    def showFrac(self):

        if len(self.matH) >= 3:
            values = [self.analH.fi, self.analH.fm, self.analH.fr]
            # label = ['Fi', 'Fm', 'Fr']
            plt.pie(values, autopct='%1.1f%%', startangle=140)
            plt.show()

        elif len(self.matH) == 2:
            values = [self.analH.fi, self.analH.fm]
            label = ['Fi', 'Fm']
            plt.pie(values, labels=label, autopct='%1.1f%%', startangle=140)
            plt.show()

    def set_analise(self):
        self.analH.analise_type = self.analise_tipo
        self.analH.geo = self.geo
        self.analH.fi = self.fi
        self.analH.fr = self.fr
        self.analH.fm = self.fm




