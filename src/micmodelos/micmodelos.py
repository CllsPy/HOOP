from abc import ABC, abstractmethod


class Micmodelos(ABC):
    """Classe base para modelos micromecânicos de homogeneização.

    Subclasses implementam calc(objH) e populam os atributos de resultado
    (self.Eh, self.vh, etc.). Use get_resultado_mecanico() /
    get_resultado_condutividade() para obter o resultado encapsulado.
    """

    def __init__(self):
        self.tipo = None
        self.status = None
        # Atributos de resultado — populados por calc() em cada subclasse
        self.Eh = None
        self.vh = None
        self.kh = None
        self.Gh = None
        self.Em = None
        self.vm = None
        self.Ei = None
        self.vi = None
        self.fi = None
        self.K11 = None
        self.K22 = None
        self.K33 = None
        self.C  = None
        self.Ci = None
        self.Cm = None

    @abstractmethod
    def calc(self, objH) -> None:
        """Executa o cálculo e popula os atributos de resultado em self."""
        ...

    def get_resultado_mecanico(self):
        """Empacota o resultado mecânico atual em um dataclass tipado.
        Compatibilidade retroativa: modelos existentes não precisam ser alterados.
        """
        from resultados.resultados import ResultadoMecanico
        return ResultadoMecanico(
            Eh=self.Eh or 0.0,
            vh=self.vh or 0.0,
            kh=self.kh or 0.0,
            Gh=self.Gh or 0.0,
            Em=self.Em or 0.0,
            fi=self.fi or 0.0,
            C=self.C,
        )

    def get_resultado_condutividade(self):
        """Empacota o resultado de condutividade atual em um dataclass tipado."""
        from resultados.resultados import ResultadoCondutividade
        return ResultadoCondutividade(
            K11=self.K11 or 0.0,
            K22=self.K22 or 0.0,
            K33=self.K33 or 0.0,
            fi=self.fi or 0.0,
            kh=self.kh,
        )
