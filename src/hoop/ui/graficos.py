"""Figuras matplotlib da Análise no estilo do DS (``st.pyplot(fig)``; feche com ``plt.close``).

- ``figura_comparacao``: faixa Voigt–Reuss, curvas dos modelos e marcador do fi lido.
- ``figura_modelo_individual``: um modelo por figura, nos ``limites_y`` comuns
  (Small Multiples).
"""
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from hoop.ui.calculo import (GRANDEZAS, LIMITES, REFERENCIA_PADRAO, CurvaModelo,
                             ResultadoAnalise, escolher_referencia, valor_em)
from hoop.ui.formatacao import formatar_decimal, formatar_numero
from hoop.ui.tema import CORES, MARCADORES, SERIES, TRACEJADOS, estilo_matplotlib

ROTULO_X = 'fração volumétrica de inclusão fi'
_MARCAR_A_CADA = 10


def _formatador(grandeza: str) -> FuncFormatter:
    casas = GRANDEZAS[grandeza].casas_eixo
    return FuncFormatter(lambda v, _: formatar_numero(v, casas))


def _configurar_eixos(ax, grandeza: str) -> None:
    ax.set_xlabel(ROTULO_X)
    ax.set_ylabel(GRANDEZAS[grandeza].rotulo)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: formatar_decimal(v, 1)))
    ax.yaxis.set_major_formatter(_formatador(grandeza))
    ax.set_xlim(left=0)


def _desenhar_faixa(ax, resultado: ResultadoAnalise, grandeza: str, rotular: bool) -> None:
    voigt, reuss = (resultado.curvas.get(n) for n in LIMITES)
    if voigt and reuss and not (voigt.vazia or reuss.vazia):
        n = min(len(voigt.fis), len(reuss.fis))
        sup, inf = voigt.valores[grandeza][:n], reuss.valores[grandeza][:n]
        ax.fill_between(voigt.fis[:n], np.minimum(sup, inf), np.maximum(sup, inf),
                        color=CORES['band-bounds'], linewidth=0, label='Faixa Voigt–Reuss')
    superior = _limite_superior(resultado, grandeza)
    for nome in LIMITES:
        curva = resultado.curvas.get(nome)
        if curva and not curva.vazia:
            ax.plot(curva.fis, curva.valores[grandeza], color=SERIES[nome],
                    linestyle='--', linewidth=1.2)
            if rotular:
                _rotular_limite(ax, curva, grandeza, acima=nome == superior)


def _limite_superior(resultado: ResultadoAnalise, grandeza: str) -> str:
    """Limite que fica por cima no gráfico (Voigt para Eh; pode inverter em νh)."""
    voigt, reuss = (resultado.curvas.get(n) for n in LIMITES)
    if voigt and reuss and not (voigt.vazia or reuss.vazia):
        meio = min(len(voigt.fis), len(reuss.fis)) // 2
        if voigt.valores[grandeza][meio] < reuss.valores[grandeza][meio]:
            return 'Reuss'
    return 'Voigt'


def _rotular_limite(ax, curva: CurvaModelo, grandeza: str, acima: bool) -> None:
    """Rótulo direto do limite onde a faixa é larga (60% do trecho calculado)."""
    i = int(len(curva.fis) * 0.6)
    ax.annotate(curva.nome, (curva.fis[i], curva.valores[grandeza][i]),
                xytext=(0, 6 if acima else -6), textcoords='offset points',
                ha='right' if acima else 'left', va='bottom' if acima else 'top',
                fontsize=9, color=CORES['ink-muted'])


def _desenhar_curva(ax, curva: CurvaModelo, grandeza: str) -> None:
    """Linha contínua dentro da validade e tracejada acima de ``fi_validade``."""
    cor, ys = SERIES[curva.nome], curva.valores[grandeza]
    estilo = dict(color=cor, linewidth=1.8, marker=MARCADORES[curva.nome],
                  markersize=5, markevery=_MARCAR_A_CADA)
    linha = TRACEJADOS.get(curva.nome, '-')
    if curva.fi_validade is None:
        ax.plot(curva.fis, ys, linestyle=linha, label=curva.nome, **estilo)
        return
    dentro = curva.fis <= curva.fi_validade + 1e-12
    ax.plot(curva.fis[dentro], ys[dentro], linestyle=linha, label=curva.nome, **estilo)
    inicio = max(int(dentro.sum()) - 1, 0)
    ax.plot(curva.fis[inicio:], ys[inicio:], color=cor, linewidth=1.4, linestyle='--')


def _desenhar_leitura(ax, resultado: ResultadoAnalise, grandeza: str,
                      fi: float, referencia: str) -> None:
    ax.axvline(fi, color=CORES['ink-muted'], linewidth=1, zorder=1)
    ax.annotate(f'fi {formatar_decimal(fi, 2)}', (fi, 1), xycoords=('data', 'axes fraction'),
                xytext=(4, -2), textcoords='offset points', va='top', fontsize=9,
                color=CORES['ink'])
    valor = valor_em(resultado, referencia, grandeza, fi)
    if valor is not None:
        ax.plot([fi], [valor], marker='o', markersize=7, color=SERIES[referencia],
                markeredgecolor=CORES['surface-1'], markeredgewidth=1.5, zorder=5)


def limites_y(resultado: ResultadoAnalise, grandeza: str) -> Tuple[float, float]:
    """Faixa y comum a todas as curvas, com 4% de folga."""
    valores = [c.valores[grandeza] for c in resultado.curvas.values() if not c.vazia]
    if not valores:
        return 0.0, 1.0
    todos = np.concatenate(valores)
    lo, hi = float(todos.min()), float(todos.max())
    folga = (hi - lo) * 0.04 or abs(hi) * 0.04 or 1.0
    return lo - folga, hi + folga


def figura_comparacao(resultado: ResultadoAnalise, grandeza: str = 'Eh',
                      fi_leitura: Optional[float] = None,
                      referencia: Optional[str] = REFERENCIA_PADRAO) -> Figure:
    """Gráfico principal: faixa Voigt–Reuss, modelos e linha vertical em ``fi_leitura``.

    ``grandeza`` é uma chave de ``hoop.ui.calculo.GRANDEZAS``; ``referencia`` é o
    modelo que recebe o ponto na leitura (veja ``calculo.escolher_referencia``).
    """
    with estilo_matplotlib():
        fig, ax = plt.subplots(figsize=(7.6, 3.8), layout='constrained')
        _desenhar_faixa(ax, resultado, grandeza, rotular=True)
        for curva in resultado.curvas.values():
            if curva.nome not in LIMITES and not curva.vazia:
                _desenhar_curva(ax, curva, grandeza)
        ref = escolher_referencia(resultado, referencia)
        if fi_leitura is not None and ref:
            _desenhar_leitura(ax, resultado, grandeza, fi_leitura, ref)
        _configurar_eixos(ax, grandeza)
        ax.set_xlim(0, resultado.entrada.fi_max * 1.02)
        if ax.get_legend_handles_labels()[0]:
            fig.legend(loc='outside lower center', ncol=5, fontsize=9)
    return fig


def figura_modelo_individual(resultado: ResultadoAnalise, nome: str, grandeza: str = 'Eh',
                             limites: Optional[Tuple[float, float]] = None) -> Figure:
    """Figura pequena de um modelo sobre a faixa Voigt–Reuss, com o nome como título."""
    with estilo_matplotlib():
        fig, ax = plt.subplots(figsize=(3.6, 2.6), layout='constrained')
        _desenhar_faixa(ax, resultado, grandeza, rotular=False)
        curva = resultado.curvas[nome]
        if nome not in LIMITES and not curva.vazia:
            _desenhar_curva(ax, curva, grandeza)
        _configurar_eixos(ax, grandeza)
        ax.set_xlim(0, resultado.entrada.fi_max * 1.02)
        ax.set_ylim(*(limites or limites_y(resultado, grandeza)))
        ax.set_title(nome, loc='left', fontsize=11, color=CORES['ink'], fontweight='bold')
    return fig
