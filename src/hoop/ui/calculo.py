"""Cálculo das curvas mostradas na interface, sem Streamlit.

``calcular(entrada)`` varre fi de 0 até ``entrada.fi_max`` em passos de 0,01
para cada modelo escolhido e devolve um ``ResultadoAnalise`` imutável. Um
modelo que falha num ponto guarda a curva até o último ponto calculado e
registra a ``Falha``; os demais modelos seguem normalmente.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Dict, Mapping, Optional, Tuple

import numpy as np

from hoop.homogenizacao.composito import Composito
from hoop.materiais.fases import FaseMecanica
from hoop.micmodelos.dilute import DiluteSuspension
from hoop.micmodelos.gsc import GSC
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.popovic import Popovic
from hoop.micmodelos.reuss import Reuss
from hoop.micmodelos.selfconsistent import SelfConsistent
from hoop.micmodelos.voigt import Voigt
from hoop.resultados.resultados import ResultadoMecanico

if TYPE_CHECKING:  # entrada.py importa este módulo; aqui o tipo serve só às anotações
    from hoop.ui.entrada import EntradaComposito

PASSO_FI = 0.01
ERROS_DE_MODELO = (ValueError, RuntimeError, ZeroDivisionError, np.linalg.LinAlgError)


@dataclass(frozen=True)
class InfoModelo:
    """Metadados de um modelo para o checklist, o gráfico e o cálculo.

    ``classe()`` cria um modelo com ``homogeneizar(composito) -> ResultadoMecanico``;
    ``abreviacao`` é o nome curto usado em métricas e cabeçalhos de tabela.
    """
    nome: str
    classe: Callable
    familia: str
    descricao: str
    fi_validade: Optional[float] = None
    abreviacao: Optional[str] = None

    @property
    def nome_curto(self) -> str:
        return self.abreviacao or self.nome


MODELOS: Dict[str, InfoModelo] = {
    info.nome: info for info in (
        InfoModelo('Voigt', Voigt, 'Limites',
                   'Limite superior. Supõe deformação uniforme.'),
        InfoModelo('Reuss', Reuss, 'Limites',
                   'Limite inferior. Supõe tensão uniforme.'),
        InfoModelo('Dilute Suspension', DiluteSuspension, 'Campo médio',
                   'Inclusões isoladas. Válido até fi ≈ 0,10.', fi_validade=0.10,
                   abreviacao='Dilute'),
        InfoModelo('Mori-Tanaka', MoriTanaka, 'Campo médio',
                   'Considera a interação entre inclusões.', abreviacao='MT'),
        InfoModelo('Self-Consistent', SelfConsistent, 'Autoconsistentes',
                   'Cada fase imersa no meio efetivo. Iterativo.', abreviacao='SC'),
        InfoModelo('GSC', GSC, 'Autoconsistentes',
                   'Esfera composta (Christensen e Lo).'),
        InfoModelo('Popovic', Popovic, 'Média',
                   'Média aritmética entre Voigt e Reuss.'),
    )
}
"""Catálogo na ordem do checklist e da legenda; a chave é o nome exibido."""

MODELOS_PADRAO: Tuple[str, ...] = ('Voigt', 'Reuss', 'Mori-Tanaka', 'Self-Consistent', 'GSC')
LIMITES: Tuple[str, str] = ('Voigt', 'Reuss')
REFERENCIA_PADRAO = 'Mori-Tanaka'


def abreviar(nome: str) -> str:
    """Nome curto do modelo ("Mori-Tanaka" -> "MT"); nomes fora do catálogo ficam iguais."""
    return MODELOS[nome].nome_curto if nome in MODELOS else nome


@dataclass(frozen=True)
class Grandeza:
    """Grandeza do eixo y e tudo o que as telas precisam saber sobre ela.

    ``casas`` vale para valores e tabelas; ``casas_eixo`` para os ticks do eixo y.
    ``extrair`` lê a grandeza de um ``ResultadoMecanico``; ``valor_na_matriz``
    dá o valor em fi = 0 a partir da entrada; ``sufixo_arquivo`` entra no nome do CSV.
    """
    chave: str
    rotulo: str
    titulo: str
    unidade: str
    casas: int
    casas_eixo: int
    simbolo: str
    sufixo_arquivo: str
    extrair: Callable[[ResultadoMecanico], float]
    valor_na_matriz: Callable[['EntradaComposito'], float]


GRANDEZAS: Dict[str, Grandeza] = {
    g.chave: g for g in (
        Grandeza('Eh', 'Eh [MPa]', 'Módulo de Young homogeneizado', 'MPa', 0, 0, 'Eh', 'eh',
                 extrair=lambda r: r.Eh, valor_na_matriz=lambda e: e.Em),
        Grandeza('Eh/Em', 'Eh / Em', 'Módulo normalizado', '', 3, 2, 'Eh/Em', 'eh-em',
                 extrair=lambda r: r.Eh / r.Em, valor_na_matriz=lambda e: 1.0),
        Grandeza('vh', 'νh', 'Coeficiente de Poisson homogeneizado', '', 3, 2, 'νh', 'vh',
                 extrair=lambda r: r.vh, valor_na_matriz=lambda e: e.vm),
    )
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
    entrada: EntradaComposito
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


def criar_composito(entrada: EntradaComposito, fi: float = 0.0) -> Composito:
    """Compósito mecânico (matriz + inclusão) descrito pela entrada, com fração ``fi``."""
    return Composito(matriz=FaseMecanica(entrada.Em, entrada.vm),
                     inclusao=FaseMecanica(entrada.Ei, entrada.vi),
                     fi=fi, geometria=entrada.geometria)


def _ler_ponto(resultado: ResultadoMecanico) -> Dict[str, float]:
    valores = {chave: float(g.extrair(resultado)) for chave, g in GRANDEZAS.items()}
    if not all(np.isfinite(v) for v in valores.values()):
        raise ValueError('O modelo devolveu um valor não finito para estes dados.')
    return valores


def calcular_modelo(entrada: EntradaComposito, info: InfoModelo) -> CurvaModelo:
    """Varre fi para um modelo; para no primeiro ponto que falhar.

    Dados inválidos (ex.: Poisson fora da faixa) viram uma ``Falha`` em fi = 0.
    """
    modelo = info.classe()
    pontos, falha = [], None
    for fi in fracoes(entrada.fi_max):
        try:
            resultado = modelo.homogeneizar(criar_composito(entrada, float(fi)))
            pontos.append((float(fi), _ler_ponto(resultado)))
        except ERROS_DE_MODELO as erro:
            falha = Falha(fi=float(fi), mensagem=str(erro))
            break
    fis = np.array([fi for fi, _ in pontos])
    valores = {chave: np.array([p[chave] for _, p in pontos]) for chave in GRANDEZAS}
    return CurvaModelo(info.nome, fis, valores, falha, info.fi_validade)


def calcular(entrada: EntradaComposito, ao_progredir: Optional[Callable[[str, int, int], None]] = None
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


def comparaveis(resultado: ResultadoAnalise) -> Tuple[str, ...]:
    """Modelos com curva que não são limites: candidatos a referência."""
    return tuple(n for n in resultado.calculados if n not in LIMITES)


def escolher_referencia(resultado: ResultadoAnalise, escolhido: Optional[str] = None
                        ) -> Optional[str]:
    """Modelo de referência: o escolhido, senão Mori-Tanaka, senão o primeiro não-limite.

    Só cai num limite (Voigt ou Reuss) se nenhum outro modelo tiver curva.
    """
    candidatos = [escolhido, REFERENCIA_PADRAO, *comparaveis(resultado), *resultado.calculados]
    return next((n for n in candidatos if n in resultado.calculados), None)
