"""O problema de homogeneização como um único objeto de valor imutável.

Um ``Composito`` reúne tudo o que um modelo micromecânico precisa: a matriz,
a inclusão, a fração volumétrica da inclusão e a geometria. Ele nasce válido
e nunca muda; para variar a fração use ``dataclasses.replace`` (ou
``com_fracao``), que cria outro compósito e o valida de novo.
"""
import math
from dataclasses import dataclass, replace
from numbers import Real
from typing import Union

import numpy as np

from hoop.materiais.fases import FaseCondutividade, FaseMecanica
from hoop.mecanico.geometria_registry import GeometriaRegistry

Fase = Union[FaseMecanica, FaseCondutividade]
TIPOS_DE_FASE = (FaseMecanica, FaseCondutividade)


@dataclass(frozen=True)
class Composito:
    """Compósito de duas fases: ``matriz`` + ``inclusao`` com fração ``fi``."""
    matriz: Fase
    inclusao: Fase
    fi: float
    geometria: str = 'esfera'

    def __post_init__(self):
        self._exigir_fases_do_mesmo_tipo()
        self._exigir_fracao_valida()
        if self.geometria not in GeometriaRegistry.nomes():
            raise ValueError(
                f"Geometria '{self.geometria}' não registrada. "
                f"Disponíveis: {GeometriaRegistry.nomes()}"
            )

    def _exigir_fases_do_mesmo_tipo(self) -> None:
        for papel in ('matriz', 'inclusao'):
            fase = getattr(self, papel)
            if not isinstance(fase, TIPOS_DE_FASE):
                raise ValueError(
                    f"{papel} deve ser FaseMecanica ou FaseCondutividade. "
                    f"Recebido: {type(fase).__name__}."
                )
        if type(self.matriz) is not type(self.inclusao):
            raise ValueError(
                "matriz e inclusao devem ser do mesmo tipo de fase. Recebido: "
                f"{type(self.matriz).__name__} e {type(self.inclusao).__name__}."
            )

    def _exigir_fracao_valida(self) -> None:
        fi = self.fi
        if isinstance(fi, bool) or not isinstance(fi, Real) or not math.isfinite(fi) \
                or not 0.0 <= fi <= 1.0:
            raise ValueError(f"fi (fração de inclusão) deve estar em [0, 1]. Recebido: {fi!r}.")

    @property
    def fm(self) -> float:
        """Fração volumétrica da matriz."""
        return 1 - self.fi

    @property
    def analise(self) -> str:
        """Tipo de análise definido pelas fases: 'mecanica' ou 'condutividade'."""
        return self.matriz.analise

    @property
    def eshelby(self) -> np.ndarray:
        """Tensor de Eshelby da inclusão ``geometria`` imersa na matriz."""
        return self.matriz.eshelby(self.geometria)

    def com_fracao(self, fi: float) -> 'Composito':
        """Outro compósito igual a este, com fração de inclusão ``fi``."""
        return replace(self, fi=fi)
