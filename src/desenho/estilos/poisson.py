from desenho.estilos.estilo_base import EstiloGrafico
from typing import Tuple


class EstiloPoisson(EstiloGrafico):
    nome = 'poisson'

    def coletar_ponto(self, objH, modelo, Fi: float) -> Tuple[float, float]:
        objH.analH.fi = Fi
        objH.analH.fm = 1 - Fi
        objH.calc()
        return Fi, objH.modH.vh

    def configurar_eixos(self, ax) -> None:
        ax.set_title('Coeficiente de Poisson Homogeneizado')
        ax.set_xlabel('Fração Volumétrica de Inclusão')
        ax.set_ylabel('vh')
