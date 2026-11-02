"""Fases de um compósito como objetos de valor imutáveis.

Uma fase nasce válida (faixas físicas conferidas no construtor) e nunca
muda. Os tensores são derivados das propriedades sob demanda, calculados uma
vez e devolvidos como arrays somente leitura, para que ninguém altere por
engano o estado de uma fase compartilhada.
"""
import math
from dataclasses import dataclass, field
from functools import cached_property
from numbers import Real

import numpy as np

from hoop.mecanico.geometria_registry import tensor_eshelby
from hoop.mecanico.tensores import tensor_hill_esfera, tensor_rigidez_isotropico

POISSON_MIN, POISSON_MAX = -1.0, 0.5


def _somente_leitura(tensor: np.ndarray) -> np.ndarray:
    tensor.flags.writeable = False
    return tensor


def _exigir_positivo(nome: str, valor) -> None:
    if isinstance(valor, bool) or not isinstance(valor, Real) or not math.isfinite(valor) \
            or valor <= 0:
        raise ValueError(f"{nome} deve ser um número finito maior que zero. Recebido: {valor!r}.")


def tensor_eshelby_condutividade(geometria: str) -> np.ndarray:
    """Tensor de Eshelby (3x3) de condutividade; só a esfera está implementada."""
    if geometria != 'esfera':
        raise NotImplementedError(
            f"Tensor de Eshelby de condutividade não implementado para a geometria "
            f"'{geometria}'. Geometrias suportadas: 'esfera'."
        )
    return np.eye(3) / 3


@dataclass(frozen=True)
class FaseMecanica:
    """Fase elástica isotrópica: módulo de Young ``E`` e coeficiente de Poisson ``v``.

    ``E`` deve ser positivo. A única exceção é o poro (fase sem rigidez,
    ``E = 0``), criado explicitamente por ``FaseMecanica.poro(v)``.
    """
    E: float
    v: float
    vazio: bool = field(default=False, repr=False)   # True só para poros (E = 0)

    analise = 'mecanica'

    def __post_init__(self):
        if self.vazio is True:
            if self.E != 0:
                raise ValueError(
                    f"Um poro tem E = 0. Recebido: E={self.E!r}. "
                    "Use FaseMecanica.poro(v) para criar poros."
                )
        elif self.vazio is not False:
            raise ValueError(f"vazio deve ser True ou False. Recebido: {self.vazio!r}.")
        elif not isinstance(self.E, bool) and isinstance(self.E, Real) and self.E == 0:
            raise ValueError(
                "E (módulo de Young) deve ser maior que zero. Recebido: 0. "
                "Para uma fase sem rigidez (poros) use FaseMecanica.poro(v)."
            )
        else:
            _exigir_positivo('E (módulo de Young)', self.E)
        if isinstance(self.v, bool) or not isinstance(self.v, Real) \
                or not POISSON_MIN < self.v < POISSON_MAX:
            raise ValueError(
                f"v (coeficiente de Poisson) deve estar em ({POISSON_MIN}, {POISSON_MAX}). "
                f"Recebido: {self.v!r}."
            )

    @classmethod
    def poro(cls, v: float = 0.2) -> 'FaseMecanica':
        """Poro: fase sem rigidez (``E = 0``). Só pode ser inclusão, nunca matriz."""
        return cls(E=0.0, v=v, vazio=True)

    @cached_property
    def L(self) -> np.ndarray:
        """Tensor constitutivo (rigidez) 6x6, somente leitura (nulo para poros)."""
        return _somente_leitura(tensor_rigidez_isotropico(self.E, self.v))

    @cached_property
    def P(self) -> np.ndarray:
        """Tensor de Hill 6x6 de uma inclusão esférica nesta fase, somente leitura."""
        if self.vazio:
            raise ValueError(
                "O tensor de Hill de um poro (E = 0) não existe: um poro não pode ser matriz. "
                "Use o poro como inclusão."
            )
        return _somente_leitura(tensor_hill_esfera(self.E, self.v))

    def eshelby(self, geometria: str) -> np.ndarray:
        """Tensor de Eshelby 6x6 de uma inclusão ``geometria`` imersa nesta fase.

        O tensor de Eshelby depende só de ``v`` e da geometria, então para um
        poro ele é montado com E = 1.
        """
        E = 1.0 if self.vazio else self.E
        return _somente_leitura(tensor_eshelby(geometria, E, self.v))


@dataclass(frozen=True)
class FaseCondutividade:
    """Fase com condutividades principais ``k11``, ``k22`` e ``k33``."""
    k11: float
    k22: float
    k33: float

    analise = 'condutividade'

    def __post_init__(self):
        for nome in ('k11', 'k22', 'k33'):
            _exigir_positivo(nome, getattr(self, nome))

    @classmethod
    def isotropica(cls, k: float) -> 'FaseCondutividade':
        return cls(k11=k, k22=k, k33=k)

    @cached_property
    def K(self) -> np.ndarray:
        """Tensor de condutividade 3x3 (diagonal), somente leitura."""
        return _somente_leitura(np.diag([self.k11, self.k22, self.k33]).astype(float))

    def eshelby(self, geometria: str) -> np.ndarray:
        """Tensor de Eshelby 3x3 de condutividade para ``geometria``."""
        return _somente_leitura(tensor_eshelby_condutividade(geometria))
