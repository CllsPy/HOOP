from abc import ABC, abstractmethod
from typing import Tuple


class EstiloGrafico(ABC):
    """Protocolo: sabe como coletar um ponto de dados e configurar os eixos.
    Para adicionar novo estilo: criar subclasse + EstiloRegistry.registrar().
    """

    @property
    @abstractmethod
    def nome(self) -> str:
        """Identificador string do estilo (ex: 'fixar_fracao')."""
        ...

    @abstractmethod
    def coletar_ponto(self, objH, modelo, Fi: float) -> Tuple[float, float]:
        """Executa objH.calc() para a fração Fi e retorna (x, y).
        Não faz plot — apenas coleta dados.
        """
        ...

    @abstractmethod
    def configurar_eixos(self, ax) -> None:
        """Aplica título, xlabel e ylabel ao eixo matplotlib recebido."""
        ...
