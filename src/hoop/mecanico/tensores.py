"""Tensores de materiais isotrópicos em notação de Voigt (6x6).

Funções puras: recebem E e v (ou um tensor) e devolvem o resultado sem
alterar estado algum.
"""
import numpy as np


def tensor_rigidez_isotropico(E, v):
    """Tensor constitutivo L (6x6) de um material isotrópico."""
    c = E / ((1 + v) * (1 - 2 * v))
    cisalhamento = (1 - 2 * v) / 2
    return c * np.array([[1 - v, v, v, 0, 0, 0],
                         [v, 1 - v, v, 0, 0, 0],
                         [v, v, 1 - v, 0, 0, 0],
                         [0, 0, 0, cisalhamento, 0, 0],
                         [0, 0, 0, 0, cisalhamento, 0],
                         [0, 0, 0, 0, 0, cisalhamento]])


def tensor_hill_esfera(E, v):
    """Tensor de Hill P (6x6) de uma inclusão esférica em meio isotrópico."""
    m = (1 + v) / (3 * (1 - v))
    n = (2 * (4 - 5 * v)) / (15 * (1 - v))
    K = E / (3 * (1 - 2 * v))
    G = E / (2 * (1 + v))

    diagonal = (1 / 3) * ((m / (3 * K)) + (n / G))
    fora_diagonal = (1 / 3) * ((m / (3 * K)) - (n / (2 * G)))
    cisalhamento = n / G
    return np.array([[diagonal, fora_diagonal, fora_diagonal, 0, 0, 0],
                     [fora_diagonal, diagonal, fora_diagonal, 0, 0, 0],
                     [fora_diagonal, fora_diagonal, diagonal, 0, 0, 0],
                     [0, 0, 0, cisalhamento, 0, 0],
                     [0, 0, 0, 0, cisalhamento, 0],
                     [0, 0, 0, 0, 0, cisalhamento]])


def propriedades_isotropicas(C, indices=(0, 1)):
    """Extrai (E, v, K, G) de um tensor constitutivo C (6x6).

    E e v saem do termo diagonal C[i, i] e do termo de acoplamento C[i, j],
    com (i, j) = indices; K (módulo volumétrico) e G (módulo cisalhante) são
    derivados de E e v. Para C isotrópico qualquer par de direções normais
    dá o mesmo resultado; para C transversalmente isotrópico (inclusões
    cilíndricas) o par escolhe o plano de onde as propriedades são lidas.
    """
    i, j = indices
    C11, C12 = C[i, i], C[i, j]
    E = (-2 * C12 ** 2 + C12 * C11 + C11 ** 2) / (C12 + C11)
    v = C12 / (C12 + C11)
    K = E / (3 * (1 - 2 * v))
    G = E / (2 * (1 + v))
    return E, v, K, G
