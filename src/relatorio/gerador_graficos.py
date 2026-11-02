import io
from typing import List, Tuple

import matplotlib.pyplot as plt
import seaborn as sns

from relatorio.extrator import DadosRelatorio

_MARCADORES = ['o', 's', '^', '*', 'x', 'D', 'p', 'h']

_TITULOS = {
    'poisson':      ('Comparacao de Modelos - Coef. de Poisson',
                     'Fracao Volumetrica de Inclusao (fi)',
                     'vh (Coef. de Poisson Homogeneizado)'),
    'normalizar':   ('Comparacao de Modelos - Modulo Normalizado',
                     'fi', 'Eh / Em'),
    'fixar_fracao': ('Comparacao de Modelos - Modulo de Elasticidade',
                     'fi', 'Eh [MPa]'),
}


def _titulo_eixos(estilo: str) -> Tuple[str, str, str]:
    return _TITULOS.get(estilo, ('Modelos', 'fi', 'y'))


def _salvar_figura(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    data = buf.getvalue()
    plt.close(fig)
    return data


def gerar_grafico_combinado(dados: DadosRelatorio) -> bytes:
    """Recria o gráfico combinado (equivalente a juntar_grafs) e retorna bytes PNG."""
    with sns.axes_style('whitegrid'):
        fig, ax = plt.subplots(figsize=(10, 5))

    titulo, xlabel, ylabel = _titulo_eixos(dados.entrada.estilo)

    for i, modelo in enumerate(dados.modelos):
        marcador = _MARCADORES[i % len(_MARCADORES)]
        ax.plot(modelo.xs, modelo.ys,
                label=modelo.nome,
                marker=marcador,
                markersize=4)

    ax.set_title(titulo)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(loc='best')
    sns.despine(ax=ax, left=True)

    return _salvar_figura(fig)


def gerar_graficos_individuais(dados: DadosRelatorio) -> List[Tuple[str, bytes]]:
    """Gera um PNG por modelo. Retorna lista de (nome, bytes_png)."""
    _, xlabel, ylabel = _titulo_eixos(dados.entrada.estilo)
    resultados = []

    for modelo in dados.modelos:
        with sns.axes_style('whitegrid'):
            fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(modelo.xs, modelo.ys, color='black', label=modelo.nome)
        ax.set_title(f'Model: {modelo.nome}')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.legend(loc='best')
        sns.despine(ax=ax, left=True)
        resultados.append((modelo.nome, _salvar_figura(fig)))

    return resultados
