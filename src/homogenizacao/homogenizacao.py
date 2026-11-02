from analise.analise import Analise
from homogenizacao.calculadora_fracoes import CalculadoraFracoes


class Homogenizacao(object):
    def __init__(self):
        self.analH = Analise('mecanica', 'esfera', 0, 0, None)
        self.modH = None
        self.matH = []
        self.tipo = None
        self.geo = None
        self.fi = 0
        self.fm = 0
        self.analise_tipo = None

    def calc(self):
        if self.tipo != 'global':
            raise ValueError(
                f"Tipo de homogeneização não suportado: '{self.tipo}'. Use tipo = 'global'."
            )
        CalculadoraFracoes.distribuir(self.analH, self.matH)

        for i, mat in enumerate(self.matH):
            mat.id = i
            mat.geo = self.analH.geo
            mat.calc()

        self.modH.calc(self)

    def set_analise(self):
        self.analH.analise_type = self.analise_tipo
        self.analH.geo = self.geo
        self.analH.fi = self.fi
        self.analH.fm = self.fm
