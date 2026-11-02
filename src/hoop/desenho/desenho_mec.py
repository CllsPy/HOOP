from contextlib import ExitStack, contextmanager
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure

from hoop.desenho.estilos.estilo_registry import EstiloRegistry
from hoop.homogenizacao.varredura import Curva, varrer

_MARCADORES = ['o', 's', '^', '*', 'x', 'D', 'p', 'h',
               '+', '|', '.', ',', '1', '2', '3', '4',
               '<', '>', 'v']

LimitesY = Optional[Tuple[float, float]]


@contextmanager
def _visual_local():
    """Aparência dos gráficos sem alterar o plt.rcParams global de quem chama."""
    with ExitStack() as pilha:
        pilha.enter_context(plt.rc_context({'font.size': 8, 'figure.figsize': (8, 4)}))
        pilha.enter_context(sns.axes_style('whitegrid'))
        pilha.enter_context(sns.color_palette('Paired'))
        yield


class DesenhoMecanico:
    """Desenha curvas propriedade homogeneizada vs. fração de inclusão.

    O cálculo fica em ``hoop.homogenizacao.varredura.varrer``; esta classe só
    desenha. Cada método cria e devolve a sua ``Figure`` (não chama
    ``plt.show()``): scripts chamam ``plt.show()`` quando quiserem janelas.
    """

    def __init__(self, estilo: str = 'fixar_fracao'):
        self.estilo = estilo or 'fixar_fracao'
        self._estilo = EstiloRegistry.obter(self.estilo)
        self.curvas: List[Curva] = []

    @property
    def graphs(self) -> List[Tuple[List[float], List[float], str]]:
        """Curvas já calculadas como tuplas (xs, ys, nome do modelo)."""
        return [(c.xs, c.ys, c.nome) for c in self.curvas]

    def desenha(self, objH, modelo, limites_y: LimitesY = None) -> Figure:
        """Varre fi de 0 até objH.fi (ou 1, se objH.fi == 0) e desenha a curva do modelo.

        ``objH`` (Homogenizacao) só fornece o compósito e o fi máximo; nem ele
        nem o modelo são alterados.
        """
        self._exigir_tipo_de_analise(objH)
        fi_max = objH.fi if objH.fi > 0 else 1.0
        curva = varrer(objH.composito(), modelo, self._estilo.extrair,
                       fi_max=fi_max, passos=max(1, round(fi_max * 100)))
        self.curvas.append(curva)

        with _visual_local():
            fig, ax = plt.subplots()
            ax.plot(curva.xs, curva.ys, label=curva.nome, color='black')
            self._finalizar_eixos(ax, f'{self._estilo.titulo} - {curva.nome}', limites_y)
        return fig

    def juntar_grafs(self, limites_y: LimitesY = None) -> Figure:
        """Sobrepõe numa nova figura todas as curvas já desenhadas."""
        with _visual_local():
            fig, ax = plt.subplots()
            for i, curva in enumerate(self.curvas):
                ax.plot(curva.xs, curva.ys, label=curva.nome,
                        marker=_MARCADORES[i % len(_MARCADORES)], markersize=5)
            self._finalizar_eixos(ax, self._estilo.titulo, limites_y)
        return fig

    def _exigir_tipo_de_analise(self, objH) -> None:
        if objH.analH.analise_type != self._estilo.analise_tipo:
            raise ValueError(
                f"O estilo '{self.estilo}' exige análise '{self._estilo.analise_tipo}', "
                f"mas a análise é '{objH.analH.analise_type}'."
            )

    def _finalizar_eixos(self, ax, titulo: str, limites_y: LimitesY) -> None:
        self._estilo.configurar_eixos(ax, titulo)
        if limites_y is not None:
            ax.set_ylim(limites_y)
        ax.legend(loc='best')
        sns.despine(ax=ax, left=True)
