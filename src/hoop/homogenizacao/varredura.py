"""Varredura da fração volumétrica de inclusão: só cálculo, sem matplotlib.

O desenho (pacote ``hoop.desenho``), o relatório e o app consomem a ``Curva``
devolvida por ``varrer``; nenhum deles precisa saber como ela foi calculada.
"""
from dataclasses import dataclass, replace
from typing import Callable, List

from hoop.homogenizacao.composito import Composito
from hoop.micmodelos.micmodelos import homogeneizar

Extrator = Callable[[object], float]
"""Lê um valor escalar (ex.: Eh, Eh/Em, vh, K11) de um ResultadoMecanico ou ResultadoCondutividade."""


@dataclass(frozen=True)
class Curva:
    xs: List[float]
    ys: List[float]
    nome: str


def varrer(composito: Composito, modelo, extrair: Extrator,
           fi_max: float = 1.0, passos: int = 100) -> Curva:
    """Calcula ``extrair(resultado)`` para fi = 0, fi_max/passos, ..., fi_max.

    Cada ponto homogeneíza uma cópia de ``composito`` com a fração trocada
    (``dataclasses.replace``); a fração do compósito-base é ignorada. Nem o
    compósito nem o modelo são alterados.
    """
    if passos < 1:
        raise ValueError(f"passos deve ser >= 1. Recebido: {passos}.")
    if not 0.0 < fi_max <= 1.0:
        raise ValueError(f"fi_max deve estar em (0, 1]. Recebido: {fi_max}.")

    xs, ys = [], []
    for i in range(passos + 1):
        fi = i / passos * fi_max
        resultado = homogeneizar(modelo, replace(composito, fi=fi))
        xs.append(fi)
        ys.append(float(extrair(resultado)))
    return Curva(xs=xs, ys=ys, nome=modelo.tipo)
