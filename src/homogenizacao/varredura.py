"""Varredura da fração volumétrica de inclusão: só cálculo, sem matplotlib.

O desenho (pacote ``desenho``), o relatório e o app consomem a ``Curva``
devolvida por ``varrer``; nenhum deles precisa saber como ela foi calculada.
"""
from dataclasses import dataclass
from typing import Callable, List

Extrator = Callable[[object], float]
"""Lê um valor escalar (ex.: Eh, Eh/Em, vh, K11) de um modelo já calculado."""


@dataclass(frozen=True)
class Curva:
    xs: List[float]
    ys: List[float]
    nome: str


def varrer(objH, modelo, extrair: Extrator,
           fi_max: float = 1.0, passos: int = 100) -> Curva:
    """Calcula ``extrair(modelo)`` para fi = 0, fi_max/passos, ..., fi_max.

    O modelo recebido guarda o resultado do último ponto (fi = fi_max).
    A fração e o modelo configurados em ``objH`` são restaurados ao final,
    então a varredura não altera a análise de quem a chamou.
    """
    if passos < 1:
        raise ValueError(f"passos deve ser >= 1. Recebido: {passos}.")
    if not 0.0 < fi_max <= 1.0:
        raise ValueError(f"fi_max deve estar em (0, 1]. Recebido: {fi_max}.")

    fi_original, fm_original = objH.analH.fi, objH.analH.fm
    modelo_original = objH.modH
    objH.modH = modelo
    xs, ys = [], []
    try:
        for i in range(passos + 1):
            fi = i / passos * fi_max
            objH.analH.fi = fi
            objH.calc()
            xs.append(fi)
            ys.append(float(extrair(modelo)))
    finally:
        objH.analH.fi, objH.analH.fm = fi_original, fm_original
        objH.modH = modelo_original

    return Curva(xs=xs, ys=ys, nome=modelo.tipo)
