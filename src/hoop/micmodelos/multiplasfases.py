"""Modelo de Múltiplas-Fases (Shi et al., 2020; seção 2.6.4.7 da tese) em forma tensorial.

Baseado na dupla inclusão de Hori e Nemat-Nasser: cada fase sólida (inclusão
e revestimento) tem o seu tensor de Eshelby, montado com o coeficiente de
Poisson dela própria; um poro usa o ν da matriz, porque o ν de um vazio não
tem sentido físico.

Segue a forma do código do autor (m_phases.py), que difere das Eqs. 150-157
impressas: os índices i/r estão trocados em relação às Eqs. 150-151 (a razão
fr / fi multiplica ΔS em A_i^D, não fi / fr em A_r^D) e a concentração é
normalizada à la Mori-Tanaka por (fm I + fi A_i^D + fr A_r^D)^-1, enquanto a
Eq. 157 impressa é diluída. É a forma que mais se aproxima da Tabela 8.

Domínio: a formulação é singular quando fi -> 0 com fr > 0 (fr / fi cresce
sem limite e ΔS não se anula). Acima de fr / fi ≈ 2 o resultado deixa de
crescer com fi e pode passar do limite de Voigt; por isso o modelo exige
fr / fi <= ``RAZAO_FR_FI_MAXIMA``. Com fr = 0 ele não se reduz ao
Mori-Tanaka de duas fases (o Eshelby da inclusão usa o ν dela, não o da
matriz).
"""
import numpy as np

from hoop.micmodelos.micmodelos import Micmodelos
from hoop.micmodelos.protocolos import ModeloTresFases

RAZAO_FR_FI_MAXIMA = 1.0
"""Maior fr / fi aceito. Numa busca com fases do concreto e aleatórias o modelo
perdeu a monotonia em fi a partir de fr / fi ≈ 2; o estudo de caso usa 0,56
(nível 1) e 0,06 (nível 2)."""


def _modulos(fase):
    """(K, G) de uma fase mecânica isotrópica; (0, 0) para um poro."""
    E, v = fase.E, fase.v
    return E / (3 * (1 - 2 * v)), E / (2 * (1 + v))


def _exigir_contraste(fase, matriz, papel: str) -> None:
    """ValueError se Cfase - Cm for singular (mesmo K ou mesmo G que a matriz)."""
    for (a, b), modulo in zip(zip(_modulos(fase), _modulos(matriz)), ('volumétrico', 'cisalhante')):
        if np.isclose(a, b, rtol=1e-9, atol=0.0):
            raise ValueError(
                f"MultiplasFases: {papel} e matriz têm o mesmo módulo {modulo}, o que torna "
                f"(C{papel[0]} - Cm) singular. Use QuatroFases ou um modelo de duas fases."
            )


def _eshelby(fase, matriz, geometria):
    """Eshelby com o ν da fase; para um poro, com o ν da matriz."""
    return matriz.eshelby(geometria) if fase.vazio else fase.eshelby(geometria)


def multiplas_fases(fi, fr, Ci, Cr, Cm, Si, Sr):
    """Tensor homogeneizado do compósito matriz + inclusão revestida (forma do m_phases.py).

    ``Si`` e ``Sr`` são os tensores de Eshelby da inclusão e do revestimento.
    Diferente das Eqs. 150-157 impressas (ver docstring do módulo): fr / fi em
    A_i^D e concentração normalizada por (fm I + fi A_i^D + fr A_r^D)^-1.
    Exige ``fi > 0`` e (Ci - Cm), (Cr - Cm) inversíveis.
    """
    I = np.eye(6)
    fm = 1 - fi - fr
    q = fr / fi
    DS = Si - Sr
    Ai = np.linalg.inv(Ci - Cm) @ Cm
    Ar = np.linalg.inv(Cr - Cm) @ Cm
    Bi = Si + Ai - DS
    Br = Sr + Ar

    Phi_r = -np.linalg.inv(Br + DS @ (Br - q * DS) @ np.linalg.inv(Bi))
    Phi_i = -np.linalg.inv(DS + Br @ np.linalg.inv(Br - q * DS) @ Bi)

    Ad_i = I + Si @ Phi_i + q * DS @ (Phi_r - Phi_i)
    Ad_r = I + Sr @ Phi_r + DS @ Phi_i
    N = np.linalg.inv(fm * I + fi * Ad_i + fr * Ad_r)
    return Cm + fi * (Ci - Cm) @ Ad_i @ N + fr * (Cr - Cm) @ Ad_r @ N


class MultiplasFases(Micmodelos, ModeloTresFases):
    """Múltiplas-Fases de Shi et al. (2020) para matriz + inclusão revestida.

    Aceita fr / fi até ``RAZAO_FR_FI_MAXIMA``; acima disso, use QuatroFases.
    """

    def __init__(self):
        super().__init__()
        self.tipo = 'Múltiplas-Fases'

    def homogeneizar(self, composito):
        matriz, inclusao, revestimento = composito.matriz, composito.inclusao, composito.revestimento
        fi, fr = composito.fi, composito.fr
        if fi == 0 and fr == 0:
            return self._resultado_do_tensor(composito, np.array(matriz.L))
        if fr > RAZAO_FR_FI_MAXIMA * fi:
            razao = 'infinita (fi = 0)' if fi == 0 else f'{fr / fi:.3g}'
            raise ValueError(
                f"Múltiplas fases só vale com o revestimento até {RAZAO_FR_FI_MAXIMA:g} vez o "
                f"volume da inclusão (fr / fi <= {RAZAO_FR_FI_MAXIMA:g}); recebido fr / fi = "
                f"{razao}. Acima disso a formulação fica instável quando fi diminui. "
                "Use Quatro fases para estes dados."
            )
        _exigir_contraste(inclusao, matriz, 'inclusao')
        _exigir_contraste(revestimento, matriz, 'revestimento')
        C = multiplas_fases(fi, fr, inclusao.L, revestimento.L, matriz.L,
                            _eshelby(inclusao, matriz, composito.geometria),
                            _eshelby(revestimento, matriz, composito.geometria))
        return self._resultado_do_tensor(composito, C)
