from hoop.analise.analise import Analise
from hoop.homogenizacao.calculadora_fracoes import CalculadoraFracoes
from hoop.homogenizacao.composito import Composito


class Homogenizacao(object):
    """Adaptador de compatibilidade da API antiga, com estado.

    Código novo deve montar um ``hoop.homogenizacao.composito.Composito`` e chamar
    ``modelo.homogeneizar(composito)``. Esta classe continua servindo os
    scripts de ``cases/``, ``Milled.py``, o pacote ``desenho`` e o relatório
    antigo: ``calc()`` monta o ``Composito`` equivalente com ``composito()`` e
    o modelo em ``modH`` guarda o resultado nos seus atributos.
    """

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
        if self.modH is None:
            raise ValueError(
                "Nenhum modelo micromecânico definido: atribua um modelo a modH "
                "(ex.: h.modH = MoriTanaka()) antes de chamar calc()."
            )
        CalculadoraFracoes.distribuir(self.analH, self.matH)

        for i, mat in enumerate(self.matH):
            mat.id = i
            mat.geo = self.analH.geo
            mat.calc()

        self.modH.calc(self)

    def composito(self) -> Composito:
        """O Composito imutável equivalente à análise atual (analH.fi, analH.geo, matH)."""
        if len(self.matH) != 2:
            raise ValueError(
                f"Número de fases não suportado: {len(self.matH)}. Apenas compósitos de "
                "2 fases (matriz + inclusão) são suportados."
            )
        matriz, inclusao = (material.como_fase() for material in self.matH)
        return Composito(matriz=matriz, inclusao=inclusao,
                         fi=self.analH.fi, geometria=self.analH.geo)

    def set_analise(self):
        self.analH.analise_type = self.analise_tipo
        self.analH.geo = self.geo
        self.analH.fi = self.fi
        self.analH.fm = self.fm
