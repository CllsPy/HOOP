import math
from abc import ABC

import numpy as np

from hoop.mecanico.tensores import propriedades_isotropicas
from hoop.micmodelos.protocolos import ModeloMecanico, ModeloCondutividade
from hoop.resultados.resultados import ResultadoCondutividade, ResultadoMecanico

_METODOS = {
    'mecanica': (ModeloMecanico, 'homogeneizar'),
    'condutividade': (ModeloCondutividade, 'homogeneizar_condutividade'),
}


def metodo_de_homogeneizacao(modelo, tipo_analise: str):
    """Método do ``modelo`` que resolve ``tipo_analise``; ValueError se ele não suporta."""
    protocolo, nome = _METODOS.get(tipo_analise, (None, None))
    if protocolo is None or not isinstance(modelo, protocolo):
        nome_modelo = getattr(modelo, 'tipo', None) or type(modelo).__name__
        raise ValueError(f"{nome_modelo}: tipo de análise não suportado: '{tipo_analise}'.")
    return getattr(modelo, nome)


def homogeneizar(modelo, composito):
    """Homogeneíza ``composito`` pelo tipo de análise que as suas fases definem.

    Devolve ``ResultadoMecanico`` ou ``ResultadoCondutividade``; nem o modelo
    nem o compósito são alterados.
    """
    return metodo_de_homogeneizacao(modelo, composito.analise)(composito)


class Micmodelos(ABC):
    """Classe base para modelos micromecânicos de homogeneização.

    API sem estado: ``homogeneizar(composito) -> ResultadoMecanico`` e
    ``homogeneizar_condutividade(composito) -> ResultadoCondutividade``,
    conforme os mixins de ``hoop.micmodelos.protocolos`` que a subclasse
    implementa. Os atributos do objeto guardam só configuração (ex.: ``tol``
    do Self-Consistent).

    Adaptador de compatibilidade: ``calc(objH)`` lê uma ``Homogenizacao``,
    delega para a API sem estado e copia o resultado para os atributos
    antigos (``Eh``, ``vh``, ``C``, ``K11``...), que scripts e desenhos
    antigos ainda leem.
    """

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

    # --- API sem estado: auxiliares das subclasses ---------------------------

    @staticmethod
    def _resultado_do_tensor(composito, C) -> ResultadoMecanico:
        """ResultadoMecanico com E, v, K e G lidos do tensor homogeneizado C.

        ValueError se o tensor não for finito ou se E sair não positivo: o
        modelo saiu do seu domínio e o número não tem sentido físico.
        """
        Eh, vh, kh, Gh = propriedades_isotropicas(C)
        if not (np.all(np.isfinite(C)) and math.isfinite(Eh) and math.isfinite(vh)):
            raise ValueError(
                f"O modelo devolveu um valor não finito em fi = {composito.fi:g}: estes dados "
                "estão fora do domínio dele. Reduza a fração ou use outro modelo."
            )
        if Eh <= 0:
            raise ValueError(
                f"O modelo prevê E nulo ou negativo em fi = {composito.fi:g} "
                f"(Eh = {Eh:.4g}), o que não tem sentido físico. Reduza a fração ou use "
                "Mori-Tanaka."
            )
        return ResultadoMecanico(Eh=Eh, vh=vh, kh=kh, Gh=Gh,
                                 Em=composito.matriz.E, fi=composito.fi, C=C)

    @staticmethod
    def _exigir_inclusao_com_rigidez(composito, nome: str, motivo: str) -> None:
        """ValueError se a inclusão for um poro (E = 0), que ``nome`` não trata."""
        if getattr(composito.inclusao, 'vazio', False):
            raise ValueError(
                f"{nome} não se aplica a poros (E = 0): {motivo}. "
                "Use Mori-Tanaka no nível dos poros."
            )

    @staticmethod
    def _resultado_condutividade(composito, kh) -> ResultadoCondutividade:
        return ResultadoCondutividade(K11=kh[0, 0], K22=kh[1, 1], K33=kh[2, 2],
                                      fi=composito.fi, kh=kh)

    # --- adaptador da API antiga ----------------------------------------------

    def calc(self, objH) -> None:
        """Calcula a análise de ``objH`` (Homogenizacao) e guarda o resultado em self."""
        tipo_analise = objH.analH.analise_type
        resolver = metodo_de_homogeneizacao(self, tipo_analise)
        composito = objH.composito()
        if composito.analise != tipo_analise:
            raise ValueError(
                f"{self.tipo}: análise '{tipo_analise}' pedida para fases de "
                f"'{composito.analise}'."
            )
        resultado = resolver(composito)
        if tipo_analise == 'mecanica':
            self._guardar_mecanico(composito, resultado)
        else:
            self._guardar_condutividade(composito, resultado)

    def _guardar_mecanico(self, composito, resultado: ResultadoMecanico) -> None:
        matriz, inclusao = composito.matriz, composito.inclusao
        self.fi = composito.fi
        self.Em, self.vm, self.Cm = matriz.E, matriz.v, matriz.L
        self.Ei, self.vi, self.Ci = inclusao.E, inclusao.v, inclusao.L
        self.C = resultado.C
        self.Eh, self.vh, self.kh, self.Gh = resultado.Eh, resultado.vh, resultado.kh, resultado.Gh

    def _guardar_condutividade(self, composito, resultado: ResultadoCondutividade) -> None:
        self.fi = composito.fi
        self.Km, self.Ki = composito.matriz.K, composito.inclusao.K
        self.kh = resultado.kh
        self.K11, self.K22, self.K33 = resultado.K11, resultado.K22, resultado.K33

    def get_resultado_mecanico(self) -> ResultadoMecanico:
        """Empacota o resultado mecânico guardado pelo último calc(objH)."""
        return ResultadoMecanico(
            Eh=self.Eh or 0.0,
            vh=self.vh or 0.0,
            kh=self.kh or 0.0,
            Gh=self.Gh or 0.0,
            Em=self.Em or 0.0,
            fi=self.fi or 0.0,
            C=self.C,
        )

    def get_resultado_condutividade(self) -> ResultadoCondutividade:
        """Empacota o resultado de condutividade guardado pelo último calc(objH)."""
        return ResultadoCondutividade(
            K11=self.K11 or 0.0,
            K22=self.K22 or 0.0,
            K33=self.K33 or 0.0,
            fi=self.fi or 0.0,
            kh=self.kh,
        )
