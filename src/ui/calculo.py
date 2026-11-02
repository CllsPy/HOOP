"""Cálculo das curvas mostradas na interface, sem Streamlit.

``calcular(entrada)`` varre fi de 0 até ``entrada.fi_max`` em passos de 0,01
para cada modelo escolhido e devolve um ``ResultadoAnalise`` imutável. Um
modelo que falha num ponto guarda a curva até o último ponto calculado e
registra a ``Falha``; os demais modelos seguem normalmente.
"""
from dataclasses import dataclass
from typing import Callable, Dict, Mapping, Optional, Tuple

import numpy as np

from homogenizacao.homogenizacao import Homogenizacao
from mecanico.mecanico import Mecanico
from micmodelos.dilute import DiluteSuspension
from micmodelos.gsc import GSC
from micmodelos.moritanaka import MoriTanaka
from micmodelos.popovic import Popovic
from micmodelos.reuss import Reuss
from micmodelos.selfconsistent import SelfConsistent
from micmodelos.voigt import Voigt

PASSO_FI = 0.01
ERROS_DE_MODELO = (ValueError, RuntimeError, ZeroDivisionError, np.linalg.LinAlgError)


@dataclass(frozen=True)
class InfoModelo:
    """Metadados de um modelo para o checklist, o gráfico e o cálculo."""
    nome: str
    classe: Callable
    familia: str
    descricao: str
    fi_validade: Optional[float] = None


MODELOS: Dict[str, InfoModelo] = {
    info.nome: info for info in (
        InfoModelo('Voigt', Voigt, 'Limites',
                   'Limite superior. Supõe deformação uniforme.'),
        InfoModelo('Reuss', Reuss, 'Limites',
                   'Limite inferior. Supõe tensão uniforme.'),
        InfoModelo('Dilute Suspension', DiluteSuspension, 'Campo médio',
                   'Inclusões isoladas. Válido até fi ≈ 0,10.', fi_validade=0.10),
        InfoModelo('Mori-Tanaka', MoriTanaka, 'Campo médio',
                   'Considera a interação entre inclusões.'),
        InfoModelo('Self-Consistent', SelfConsistent, 'Autoconsistentes',
                   'Cada fase imersa no meio efetivo. Iterativo.'),
        InfoModelo('GSC', GSC, 'Autoconsistentes',
                   'Esfera composta (Christensen e Lo).'),
        InfoModelo('Popovic', Popovic, 'Média',
                   'Média aritmética entre Voigt e Reuss.'),
    )
}
"""Catálogo na ordem do checklist e da legenda; a chave é o nome exibido."""

MODELOS_PADRAO: Tuple[str, ...] = ('Voigt', 'Reuss', 'Mori-Tanaka', 'Self-Consistent', 'GSC')
LIMITES: Tuple[str, str] = ('Voigt', 'Reuss')


@dataclass(frozen=True)
class Grandeza:
    """Grandeza do eixo y: chave, rótulo de eixo, título, unidade, casas decimais e símbolo."""
    chave: str
    rotulo: str
    titulo: str
    unidade: str
    casas: int
    simbolo: str


GRANDEZAS: Dict[str, Grandeza] = {
    g.chave: g for g in (
        Grandeza('Eh', 'Eh [MPa]', 'Módulo de Young homogeneizado', 'MPa', 0, 'Eh'),
        Grandeza('Eh/Em', 'Eh / Em', 'Módulo normalizado', '', 3, 'Eh/Em'),
        Grandeza('vh', 'νh', 'Coeficiente de Poisson homogeneizado', '', 3, 'νh'),
    )
}

_EXTRATORES: Dict[str, Callable[[object], float]] = {
    'Eh': lambda m: m.Eh,
    'Eh/Em': lambda m: m.Eh / m.Em,
    'vh': lambda m: m.vh,
}


@dataclass(frozen=True)
class Falha:
    """Um modelo parou em ``fi``; ``mensagem`` vem do erro do domínio."""
    fi: float
    mensagem: str


@dataclass(frozen=True)
class CurvaModelo:
    """Curvas de um modelo: ``fis`` e, para cada grandeza, os valores nesses fi."""
    nome: str
    fis: np.ndarray
    valores: Mapping[str, np.ndarray]
    falha: Optional[Falha] = None
    fi_validade: Optional[float] = None

    @property
    def vazia(self) -> bool:
        return len(self.fis) == 0

    def valido_em(self, fi: float) -> bool:
        """True se ``fi`` está dentro da faixa de validade do modelo."""
        return self.fi_validade is None or fi <= self.fi_validade + 1e-12


@dataclass(frozen=True)
class ResultadoAnalise:
    """Resultado de ``calcular``: a entrada usada e uma curva por modelo, na ordem pedida."""
    entrada: object
    curvas: Mapping[str, CurvaModelo]

    @property
    def falhas(self) -> Dict[str, Falha]:
        return {nome: c.falha for nome, c in self.curvas.items() if c.falha}

    @property
    def calculados(self) -> Tuple[str, ...]:
        """Modelos com ao menos um ponto calculado."""
        return tuple(nome for nome, c in self.curvas.items() if not c.vazia)


def fracoes(fi_max: float) -> np.ndarray:
    """Pontos de fi de 0 a ``fi_max`` com passo 0,01 (101 pontos para fi_max = 1)."""
    passos = max(1, int(round(fi_max / PASSO_FI)))
    return np.linspace(0.0, fi_max, passos + 1)


def criar_homogenizacao(entrada) -> Homogenizacao:
    """Monta a Homogenizacao com matriz e inclusão a partir da entrada."""
    h = Homogenizacao()
    h.tipo = 'global'
    h.analise_tipo = entrada.tipo_analise
    h.geo = entrada.geometria
    h.Em, h.vm, h.Ei, h.vi = entrada.Em, entrada.vm, entrada.Ei, entrada.vi
    h.set_analise()
    for E, v in ((entrada.Em, entrada.vm), (entrada.Ei, entrada.vi)):
        fase = Mecanico()
        fase.E, fase.v, fase.geo = E, v, entrada.geometria
        h.matH.append(fase)
    return h


def _ler_ponto(modelo) -> Dict[str, float]:
    valores = {chave: float(extrair(modelo)) for chave, extrair in _EXTRATORES.items()}
    if not all(np.isfinite(v) for v in valores.values()):
        raise ValueError('O modelo devolveu um valor não finito para estes dados.')
    return valores


def calcular_modelo(entrada, info: InfoModelo) -> CurvaModelo:
    """Varre fi para um modelo; para no primeiro ponto que falhar."""
    h = criar_homogenizacao(entrada)
    modelo = info.classe()
    h.modH = modelo
    pontos, falha = [], None
    for fi in fracoes(entrada.fi_max):
        h.analH.fi = float(fi)
        try:
            h.calc()
            pontos.append((float(fi), _ler_ponto(modelo)))
        except ERROS_DE_MODELO as erro:
            falha = Falha(fi=float(fi), mensagem=str(erro))
            break
    fis = np.array([fi for fi, _ in pontos])
    valores = {chave: np.array([p[chave] for _, p in pontos]) for chave in _EXTRATORES}
    return CurvaModelo(info.nome, fis, valores, falha, info.fi_validade)


def calcular(entrada, ao_progredir: Optional[Callable[[str, int, int], None]] = None
             ) -> ResultadoAnalise:
    """Calcula as curvas de todos os modelos de ``entrada.modelos``.

    ``ao_progredir(nome, concluidos, total)`` é chamado antes de cada modelo,
    com o número de modelos já prontos, para alimentar uma barra de progresso.
    """
    nomes = tuple(entrada.modelos)
    curvas = {}
    for i, nome in enumerate(nomes):
        if ao_progredir:
            ao_progredir(nome, i, len(nomes))
        curvas[nome] = calcular_modelo(entrada, MODELOS[nome])
    return ResultadoAnalise(entrada=entrada, curvas=curvas)


def valor_em(resultado: ResultadoAnalise, modelo: str, grandeza: str, fi: float
             ) -> Optional[float]:
    """Valor interpolado de ``grandeza`` em ``fi``; None se o modelo não chegou a esse fi."""
    curva = resultado.curvas.get(modelo)
    if curva is None or curva.vazia or fi > curva.fis[-1] + 1e-12 or fi < 0:
        return None
    return float(np.interp(fi, curva.fis, curva.valores[grandeza]))
