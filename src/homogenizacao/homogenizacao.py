from analise import Analise
from micmodelos import Micmodelos
from mecanico import Mecanico
from materiais import Materiais
import matplotlib.pyplot as plt

class Homogenizacao (object):
    def __init__(self):
        self.analH = Analise
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

    def calcB(self):  # <------- FUNCIONANDO =======================
        if len(self.matH) == 2:
            self.matH[0].fk = 1 - self.analH.fi
            self.matH[1].fk = self.analH.fi
            self.analH.fm = 1 - self.analH.fi

        elif len(self.matH) == 3:  # <------- FALTA TESTAR =======================
            self.matH[0].fk = self.analH.fm
            self.matH[1].fk = self.analH.fi
            self.matH[2].fk = 1 - self.analH.fi - self.analH.fm
            self.analH.fr = 1 - self.analH.fi - self.analH.fm

        for i in range(len(self.matH)):  # <------- FALTA TESTAR =======================
            self.matH[i].id = i
            self.matH[i].geo = self.analH.geo
            self.matH[i].calc()

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




