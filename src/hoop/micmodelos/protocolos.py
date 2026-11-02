from abc import ABC, abstractmethod

from hoop.resultados.resultados import ResultadoCondutividade, ResultadoMecanico


class ModeloMecanico(ABC):
    """Mixin: modelo que suporta análise mecânica."""

    @abstractmethod
    def homogeneizar(self, composito) -> ResultadoMecanico:
        """Homogeneíza um Composito de fases mecânicas, sem alterar estado algum."""
        ...


class ModeloCondutividade(ABC):
    """Mixin: modelo que suporta análise de condutividade térmica."""

    @abstractmethod
    def homogeneizar_condutividade(self, composito) -> ResultadoCondutividade:
        """Homogeneíza um Composito de fases de condutividade, sem alterar estado algum."""
        ...
