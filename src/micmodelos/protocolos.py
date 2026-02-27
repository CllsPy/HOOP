from abc import ABC, abstractmethod


class ModeloMecanico(ABC):
    """Mixin: modelo que suporta análise mecânica.
    Implementar calc_mecanico(objH) em vez do if/elif dentro de calc().
    """

    @abstractmethod
    def calc_mecanico(self, objH) -> None:
        """Lê objH.matH e objH.analH; popula self.Eh, self.vh, self.kh, self.Gh."""
        ...


class ModeloCondutividade(ABC):
    """Mixin: modelo que suporta análise de condutividade térmica.
    Implementar calc_condutividade(objH) em vez do if/elif dentro de calc().
    """

    @abstractmethod
    def calc_condutividade(self, objH) -> None:
        """Lê objH.matH e objH.analH; popula self.K11, self.K22, self.K33."""
        ...
