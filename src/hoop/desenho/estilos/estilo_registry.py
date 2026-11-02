from hoop.desenho.estilos.estilo_base import EstiloGrafico
from typing import Dict, List


class EstiloRegistry:
    """Registry de estilos de gráfico. Para adicionar novo estilo:
       EstiloRegistry.registrar(MeuEstilo())
    """
    _registro: Dict[str, EstiloGrafico] = {}

    @classmethod
    def registrar(cls, estilo: EstiloGrafico) -> None:
        cls._registro[estilo.nome] = estilo

    @classmethod
    def obter(cls, nome: str) -> EstiloGrafico:
        if nome not in cls._registro:
            raise ValueError(
                f"Estilo '{nome}' não registrado. "
                f"Disponíveis: {list(cls._registro.keys())}"
            )
        return cls._registro[nome]

    @classmethod
    def nomes(cls) -> List[str]:
        return list(cls._registro.keys())


# Auto-registro dos estilos padrão
from hoop.desenho.estilos.fixar_fracao import EstiloFixarFracao
from hoop.desenho.estilos.poisson import EstiloPoisson
from hoop.desenho.estilos.normalizar import EstiloNormalizar
from hoop.desenho.estilos.condutividade import DIRECOES, EstiloCondutividade

EstiloRegistry.registrar(EstiloFixarFracao())
EstiloRegistry.registrar(EstiloPoisson())
EstiloRegistry.registrar(EstiloNormalizar())
for _direcao in DIRECOES:
    EstiloRegistry.registrar(EstiloCondutividade(_direcao))
