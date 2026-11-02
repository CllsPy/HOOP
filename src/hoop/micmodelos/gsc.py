import numpy as np

from hoop.mecanico.tensores import tensor_rigidez_isotropico
from hoop.micmodelos.micmodelos import Micmodelos
from hoop.micmodelos.protocolos import ModeloMecanico, ModeloCondutividade
from hoop.micmodelos.selfconsistent import condutividade_autoconsistente
from hoop.resultados.resultados import ResultadoMecanico


class GSC(Micmodelos, ModeloMecanico, ModeloCondutividade):
    """Generalized Self-Consistent (Christensen & Lo) para inclusões esféricas."""

    def __init__(self):
        super().__init__()
        self.tipo = 'GSC'

    def homogeneizar(self, composito):
        matriz, inclusao = composito.matriz, composito.inclusao
        fi, Em, vm, Ei, vi = composito.fi, matriz.E, matriz.v, inclusao.E, inclusao.v

        Ki = Ei / (3 * (1 - 2 * vi))
        Gi = Ei / (2 * (1 + vi))
        Km = Em / (3 * (1 - 2 * vm))
        Gm = Em / (2 * (1 + vm))

        g = Gi / Gm  # contraste de rigidez ao cisalhamento
        n1 = (g - 1) * (49 - 50 * vi * vm) + 35 * (g) * (vi - 2 * vm) + 35 * (2 * vi - vm)
        n2 = 5 * vi * (g - 8) + 7 * (g + 4)
        n3 = (g) * (8 - 10 * vm) + (7 - 5 * vm)

        A = 8 * (g - 1) * (4 - 5 * vm) * n1 * (fi ** (10 / 3)) - 2 * (
                    63 * (g - 1) * n2 + 2 * n1 * n3) * (fi ** (7 / 3)) + \
            252 * (g - 1) * n2 * (fi ** (5 / 3)) - 50 * (g - 1) * (7 - 12 * vm + 8 * vm ** 2) * n2 * fi + \
            4 * (7 - 10 * vm) * n2 * n3

        B = -2 * (g - 1) * (1 - 5 * vm) * n1 * (fi ** (10 / 3)) + 2 * (
                    63 * (g - 1) * n2 + 2 * n1 * n3) * (fi ** (7 / 3)) - \
            252 * (g - 1) * n2 * (fi ** (5 / 3)) + 75 * (g - 1) * (3 - vm) * vm * n2 * fi + \
            1.5 * (15 * vm - 7) * n2 * n3

        D = 4 * (g - 1) * (5 * vm - 7) * n1 * (fi ** (10 / 3)) - 2 * (
                    63 * (g - 1) * n2 + 2 * n1 * n3) * (fi ** (7 / 3)) + \
            252 * (g - 1) * n2 * (fi ** (5 / 3)) + 25 * (g - 1) * (vm ** 2 - 7) * n2 * fi - \
            (7 + 5 * vm) * n2 * n3

        K = (Km + fi * (Ki - Km) * (3 * Km + 4 * Gm) / (3 * Km + 4 * Gm + 3 * (1 - fi) * (Ki - Km)))

        delta = (2 * B / Gm) ** 2 - 4 * (A * D / Gm ** 2)
        if delta < 0:
            raise ValueError(
                f"GSC: equação quadrática em G sem raiz real (delta={delta:.4g}) "
                f"para fi={fi}, Em={Em}, vm={vm}, Ei={Ei}, vi={vi}."
            )
        G = (-(2 * B / Gm) + np.sqrt(delta)) / (2 * (A / Gm ** 2))

        E = 9 * K * G / (G + 3 * K)
        v = (3 * K - 2 * G) / (2 * (G + 3 * K))
        return ResultadoMecanico(Eh=E, vh=v, kh=K, Gh=G, Em=Em, fi=fi,
                                 C=tensor_rigidez_isotropico(E, v))

    def homogeneizar_condutividade(self, composito):
        kh = condutividade_autoconsistente(composito.fi, composito.inclusao.K, composito.matriz.K)
        return self._resultado_condutividade(composito, kh)
