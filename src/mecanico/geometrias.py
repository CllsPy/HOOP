from abc import ABC, abstractmethod
import numpy as np
import math


class GeometriaEshelby(ABC):
    """Protocolo: calcula o tensor de Eshelby S (6x6) para uma dada geometria de inclusão."""

    @property
    @abstractmethod
    def nome(self) -> str: ...

    @abstractmethod
    def calcular_S(self, E: float, v: float,
                   P: np.ndarray, L: np.ndarray) -> np.ndarray:
        """Retorna tensor S (6x6) para esta geometria."""
        ...


class GeometriaEsfera(GeometriaEshelby):
    nome = 'esfera'

    def calcular_S(self, E: float, v: float,
                   P: np.ndarray, L: np.ndarray) -> np.ndarray:
        return np.dot(P, L)


class GeometriaCilindro(GeometriaEshelby):
    nome = 'cilindro'

    def calcular_S(self, E: float, v: float,
                   P: np.ndarray, L: np.ndarray) -> np.ndarray:
        S = np.zeros((6, 6))
        k = 0.03 / 100
        S[0, 0] = ((2.0 - v) / (1.0 - v)) * (k ** 2) * (
            math.log(2.0 / k) - ((5.0 - 2.0 * v) / (4.0 - 2.0 * v)))
        S[0, 1] = -((1.0 - 2.0 * v) / (2.0 - 2.0 * v)) * (k ** 2) * (
            math.log(2.0 / k) - ((3.0 - 4.0 * v) / (2.0 - 4.0 * v)))
        S[0, 2] = S[0, 1]
        S[1, 0] = ((v) / (2.0 - 2.0 * v)) - ((1.0 + v) / (2.0 - 2.0 * v)) * (k ** 2) * (
            math.log(2.0 / k) - ((3.0 + 2.0 * v) / (2.0 + 2.0 * v)))
        S[1, 1] = ((5.0 - 4.0 * v) / (8.0 - 8.0 * v)) - ((1.0 - 2.0 * v) / (4.0 - 4.0 * v)) * (k ** 2) * (
            math.log(2.0 / k) - ((1.0 - 8.0 * v) / (4.0 - 8.0 * v)))
        S[1, 2] = -((1.0 - 4.0 * v) / (8.0 - 8.0 * v)) - ((1.0 - 2.0 * v) / (4.0 - 4.0 * v)) * (k ** 2) * (
            math.log(2.0 / k) - ((5.0 - 8.0 * v) / (4.0 - 8.0 * v)))
        S[2, 0] = S[1, 0]
        S[2, 1] = S[1, 2]
        S[2, 2] = S[1, 1]
        S[3, 3] = (3.0 - 4.0 * v) / (2 * (4.0 - 4.0 * v))
        S[4, 4] = 1.0 / 4.0
        S[5, 5] = 1.0 / 4.0
        return S


class GeometriaDisco(GeometriaEshelby):
    nome = 'disco'

    def calcular_S(self, E: float, v: float,
                   P: np.ndarray, L: np.ndarray) -> np.ndarray:
        S = np.zeros((6, 6))
        c0 = E * (1 - v) / (1 - v - 2 * v * v)
        c1 = E * v / (1 - v - 2 * v * v)
        S[2, 0] = c1 / c0
        S[2, 1] = c1 / c0
        S[2, 2] = 1.0
        S[3, 3] = 0.5
        S[4, 4] = 0.5
        return S
