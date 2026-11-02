"""O problema de homogeneização como um único objeto de valor imutável.

Um ``Composito`` reúne tudo o que um modelo micromecânico precisa: a matriz,
a inclusão, a fração volumétrica da inclusão e a geometria. Ele nasce válido
e nunca muda; para variar a fração use ``dataclasses.replace`` (ou
``com_fracao``), que cria outro compósito e o valida de novo.

``CompositoRevestido`` é o equivalente de três fases (matriz + inclusão
envolvida por um revestimento), usado pelos modelos de Quatro-Fases e de
Múltiplas-Fases.
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


def _exigir_fracao(nome: str, valor) -> None:
    if isinstance(valor, bool) or not isinstance(valor, Real) or not math.isfinite(valor) \
            or not 0.0 <= valor <= 1.0:
        raise ValueError(f"{nome} deve estar em [0, 1]. Recebido: {valor!r}.")


def _exigir_geometria(geometria: str) -> None:
    if geometria not in GeometriaRegistry.nomes():
        raise ValueError(
            f"Geometria '{geometria}' não registrada. "
            f"Disponíveis: {GeometriaRegistry.nomes()}"
        )


def _exigir_matriz_com_rigidez(matriz) -> None:
    if getattr(matriz, 'vazio', False):
        raise ValueError(
            "A matriz não pode ser um poro (E = 0): não haveria meio para transmitir "
            "esforços. Use o poro como inclusão."
        )


def _exigir_parte_solida(fracao_vazia: float) -> None:
    """ValueError se os poros ocupam o compósito inteiro."""
    if fracao_vazia >= 1.0 - 1e-12:
        raise ValueError(
            "Com essas frações o compósito seria só vazio (poros ocupando 100%) e não "
            "teria rigidez. Use uma fração de poros menor que 1."
        )


@dataclass(frozen=True)
class Composito:
    """Compósito de duas fases: ``matriz`` + ``inclusao`` com fração ``fi``."""
    matriz: Fase
    inclusao: Fase
    fi: float
    geometria: str = 'esfera'

    def __post_init__(self):
        self._exigir_fases_do_mesmo_tipo()
        _exigir_matriz_com_rigidez(self.matriz)
        _exigir_fracao('fi (fração de inclusão)', self.fi)
        if getattr(self.inclusao, 'vazio', False):
            _exigir_parte_solida(self.fi)
        _exigir_geometria(self.geometria)

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


@dataclass(frozen=True)
class CompositoRevestido:
    """Compósito de três fases: ``matriz`` + ``inclusao`` envolvida por ``revestimento``.

    ``fi`` e ``fr`` são as frações volumétricas da inclusão e do revestimento
    no compósito; a matriz ocupa o resto (``fm = 1 - fi - fr``).
    """
    matriz: FaseMecanica
    inclusao: FaseMecanica
    revestimento: FaseMecanica
    fi: float
    fr: float
    geometria: str = 'esfera'

    analise = 'mecanica'

    def __post_init__(self):
        for papel in ('matriz', 'inclusao', 'revestimento'):
            fase = getattr(self, papel)
            if not isinstance(fase, FaseMecanica):
                raise ValueError(
                    f"{papel} deve ser FaseMecanica (o compósito revestido só tem análise "
                    f"mecânica). Recebido: {type(fase).__name__}."
                )
        _exigir_matriz_com_rigidez(self.matriz)
        _exigir_fracao('fi (fração de inclusão)', self.fi)
        _exigir_fracao('fr (fração de revestimento)', self.fr)
        if self.fi + self.fr > 1.0 + 1e-12:
            raise ValueError(
                f"fi + fr deve ser no máximo 1 (a matriz ocupa o resto). "
                f"Recebido: fi={self.fi!r}, fr={self.fr!r}. Reduza uma das frações."
            )
        _exigir_parte_solida(self.fi * self.inclusao.vazio + self.fr * self.revestimento.vazio)
        _exigir_geometria(self.geometria)

    @property
    def fm(self) -> float:
        """Fração volumétrica da matriz."""
        return max(0.0, 1 - self.fi - self.fr)
