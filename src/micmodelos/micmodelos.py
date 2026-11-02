from abc import ABC

from mecanico.tensores import propriedades_isotropicas
from micmodelos.protocolos import ModeloMecanico, ModeloCondutividade


class Micmodelos(ABC):
    """Classe base para modelos micromecânicos de homogeneização.

    calc(objH) despacha pelo tipo de análise (objH.analH.analise_type) para
    calc_mecanico / calc_condutividade, conforme os mixins de
    micmodelos.protocolos que a subclasse implementa. Use
    get_resultado_mecanico() / get_resultado_condutividade() para obter o
    resultado encapsulado.
    """

    _ANALISES = {
        'mecanica': (ModeloMecanico, 'calc_mecanico'),
        'condutividade': (ModeloCondutividade, 'calc_condutividade'),
    }

    def __init__(self):
        self.tipo = None
        self.fi = None   # fração volumétrica da inclusão
        # Mecânica: fases e resultado homogeneizado
        self.Em = None
        self.vm = None
        self.Cm = None
        self.Ei = None
        self.vi = None
        self.Ci = None
        self.C = None
        self.Eh = None
        self.vh = None
        self.kh = None   # módulo volumétrico (mecânica) ou tensor de condutividade
        self.Gh = None
        # Condutividade: fases e componentes principais do resultado
        self.Km = None
        self.Ki = None
        self.K11 = None
        self.K22 = None
        self.K33 = None

    def calc(self, objH) -> None:
        """Executa o cálculo do tipo de análise pedido e popula os resultados em self."""
        tipo_analise = objH.analH.analise_type
        protocolo, metodo = self._ANALISES.get(tipo_analise, (None, None))
        if protocolo is None or not isinstance(self, protocolo):
            raise ValueError(f"{self.tipo}: tipo de análise não suportado: '{tipo_analise}'.")
        getattr(self, metodo)(objH)

    def _ler_fases_mecanicas(self, objH):
        """Registra fi e as propriedades da matriz (matH[0]) e da inclusão (matH[1])."""
        matriz, inclusao = objH.matH[0], objH.matH[1]
        self.fi = objH.analH.fi
        self.Em, self.vm, self.Cm = matriz.E, matriz.v, matriz.L
        self.Ei, self.vi, self.Ci = inclusao.E, inclusao.v, inclusao.L

    def _registrar_tensor_mecanico(self, C):
        self.C = C
        self.Eh, self.vh, self.kh, self.Gh = propriedades_isotropicas(C)

    def _ler_fases_condutividade(self, objH):
        self.fi = objH.analH.fi
        self.Km = objH.matH[0].K
        self.Ki = objH.matH[1].K

    def _registrar_tensor_condutividade(self, kh):
        self.kh = kh
        self.K11, self.K22, self.K33 = kh[0, 0], kh[1, 1], kh[2, 2]

    def get_resultado_mecanico(self):
        """Empacota o resultado mecânico atual em um dataclass tipado."""
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
