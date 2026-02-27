from desenho.estilos.estilo_base import EstiloGrafico
from typing import Tuple


class EstiloNormalizar(EstiloGrafico):
    nome = 'normalizar'

    def coletar_ponto(self, objH, modelo, Fi: float) -> Tuple[float, float]:
        objH.analH.fi = Fi
        objH.analH.fm = 1 - Fi
        objH.calc()
        return Fi, objH.modH.Eh / objH.modH.Em

    def configurar_eixos(self, ax) -> None:
        ax.set_title('Módulo Normalizado')
        ax.set_xlabel('Fração Vol. Inclusão')
        ax.set_ylabel('Eh / Em')
