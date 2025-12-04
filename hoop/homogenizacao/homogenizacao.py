import sys
sys.path.append('hoop')

from analise.analise import Analise
from micmodelos.micmodelos import Micmodelos

class Homogenizacao:
    def __init__(self, geo, fi, fm, material_tipo, fr=None, analise_tipo='global'):
        self.geo = geo
        self.fi = fi
        self.fm = fm
        self.fr = fr
        self.material_tipo = material_tipo
        self.analise_tipo = analise_tipo
        self.modelo = None
        self.materiais = []


    def calc(self):
        if self.analise_tipo == 'global':    # <------- FUNCIONANDO =======================
            self.calcB()


        elif self.analise_tipo == 'local':
            pass

    def calcB(self):  # <------- FUNCIONANDO =======================
        if len(self.materiais) == 2:
            fm_corr, fi_corr = Analise.calcFracGlobal(self.fm, self.fi)
            self.materiais[0].fk = fm_corr
            self.materiais[1].fk = fi_corr


        elif len(self.materiais) == 3:  # <------- FALTA TESTAR =======================
            fi_c, fm_c, fr_c = Analise.corrigeFracs(self.fi, self.fm, self.fr)
            self.materiais[0].fk = fm_c
            self.materiais[1].fk = fi_c
            self.materiais[2].fk = fr_c

        for mat in self.materiais:
            mat.geo = self.geo
            mat.calc()

        if self.modelo is None:
            self.modelo = Micmodelos()
        self.modelo.calc(self)



if __name__ == "__main__":
    # Inicializar com parâmetros
    h1 = Homogenizacao(
        geo="esfera",
        fi=0.6,  # definir fração volumétrica da fibra/inclusão
        fm=0.4,  # fração da matriz
        analise_tipo="global"
    )

    print(h1.calcB())
