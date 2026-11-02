import numpy as np

from mecanico.tensores import propriedades_isotropicas
from micmodelos.micmodelos import Micmodelos
from micmodelos.protocolos import ModeloMecanico, ModeloCondutividade

TOLERANCIA_PADRAO = 1e-8   # erro relativo de E entre iterações
MAX_ITER_PADRAO = 500
PLANO_TRANSVERSAL = (2, 1)  # (diagonal, acoplamento) de C lidos durante a iteração


def condutividade_autoconsistente(fi, Ki, Km):
    """Solução fechada do Self-Consistent para condutividade com inclusões esféricas."""
    b = (3 * fi - 1) * Ki + (3 * (1 - fi) - 1) * Km
    return (1 / 4) * (b + np.sqrt(b ** 2 + 8 * Km * Ki))


class SelfConsistent(Micmodelos, ModeloMecanico, ModeloCondutividade):
    def __init__(self):
        super().__init__()
        self.tipo = 'Self-Consistent'
        self.tol = TOLERANCIA_PADRAO
        self.max_iter = MAX_ITER_PADRAO

    def calc_mecanico(self, objH):
        """Itera C até o ponto fixo, recalculando o tensor de Eshelby no meio efetivo."""
        self._ler_fases_mecanicas(objH)
        fi, Cm, Ci = self.fi, self.Cm, self.Ci
        matriz = objH.matH[0]
        S = matriz.S
        I = np.eye(6)

        Co = Cm
        erro = np.inf
        iteracoes = 0
        while erro > self.tol:
            # Forma simétrica C = (Σ fr Cr Ar)(Σ fr Ar)^-1: mesmo ponto fixo que
            # Cm + fi (Ci - Cm) Ai, mas converge também para inclusões mais flexíveis que a matriz
            Ai = np.linalg.inv(I + S @ np.linalg.inv(Co) @ (Ci - Co))
            Am = np.linalg.inv(I + S @ np.linalg.inv(Co) @ (Cm - Co))
            C = (fi * Ci @ Ai + (1 - fi) * Cm @ Am) @ np.linalg.inv(fi * Ai + (1 - fi) * Am)

            E, v, _, _ = propriedades_isotropicas(C, PLANO_TRANSVERSAL)
            E_anterior = propriedades_isotropicas(Co, PLANO_TRANSVERSAL)[0]
            S = matriz.montaS(E, v)
            erro = abs(abs(E) - abs(E_anterior)) / abs(E_anterior)

            Co = C
            iteracoes += 1
            if erro > self.tol and iteracoes >= self.max_iter:
                raise RuntimeError(
                    f"Self-Consistent não convergiu em {self.max_iter} iterações (erro={erro:.3g})."
                )

        self._registrar_tensor_mecanico(C)

    def calc_condutividade(self, objH):
        self._ler_fases_condutividade(objH)
        self._registrar_tensor_condutividade(condutividade_autoconsistente(self.fi, self.Ki, self.Km))
