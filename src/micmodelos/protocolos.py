from abc import ABC, abstractmethod


class ModeloMecanico(ABC):
    """Mixin: modelo que suporta análise mecânica."""

    @abstractmethod
    def calc_mecanico(self, objH) -> None:
        """Lê objH.matH e objH.analH; popula self.C, self.Eh, self.vh, self.kh, self.Gh."""
        ...


class ModeloCondutividade(ABC):
    """Mixin: modelo que suporta análise de condutividade térmica."""

    @abstractmethod
    def calc_condutividade(self, objH) -> None:
        """Lê objH.matH e objH.analH; popula self.kh, self.K11, self.K22, self.K33."""
        ...
