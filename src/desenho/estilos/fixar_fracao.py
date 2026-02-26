from desenho.estilos.estilo_base import EstiloGrafico
from typing import Tuple


class EstiloFixarFracao(EstiloGrafico):
    nome = 'fixar_fracao'

    def coletar_ponto(self, objH, modelo, Fi: float) -> Tuple[float, float]:
        objH.analH.fi = Fi
        objH.analH.fm = 1 - Fi
        objH.calc()
        return Fi, objH.modH.Eh

    def configurar_eixos(self, ax) -> None:
        ax.set_title('Módulo de Elasticidade Homogeneizado')
        ax.set_xlabel('Fração Volumétrica de Inclusão')
        ax.set_ylabel('Eh')
