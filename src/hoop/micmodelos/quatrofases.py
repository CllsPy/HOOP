"""Modelo de Quatro-Fases (Li et al., 1999) para inclusões esféricas revestidas.

Duas aplicações do Generalized Self-Consistent (Eqs. 146-148 da tese):
primeiro a inclusão é homogeneizada com o seu revestimento, com a fração
corrigida fi / (fi + fr); a esfera resultante ("revestimento homogeneizado")
é então homogeneizada com a matriz, com fração fi + fr.
"""
from dataclasses import replace

from hoop.homogenizacao.composito import Composito
from hoop.materiais.fases import FaseMecanica
from hoop.micmodelos.gsc import GSC
from hoop.micmodelos.micmodelos import Micmodelos
from hoop.micmodelos.protocolos import ModeloTresFases


class QuatroFases(Micmodelos, ModeloTresFases):
    """Quatro-Fases de Li et al. (1999): GSC(revestimento + inclusão) e depois GSC(matriz + núcleo)."""

    def __init__(self):
        super().__init__()
        self.tipo = 'Quatro-Fases'

    def homogeneizar(self, composito):
        if composito.geometria != 'esfera':
            raise ValueError(
                f"Quatro-Fases só trata inclusões esféricas (usa o GSC). "
                f"Recebido: '{composito.geometria}'. Use geometria='esfera'."
            )
        if composito.revestimento.vazio:
            raise ValueError(
                "Quatro-Fases não aceita revestimento poroso (E = 0): o revestimento faz "
                "papel de matriz no primeiro passo. Use MultiplasFases."
            )
        gsc = GSC()
        nucleo = self.nucleo_homogeneizado(composito, gsc)
        externo = gsc.homogeneizar(
            Composito(composito.matriz, nucleo, composito.fi + composito.fr))
        return replace(externo, fi=composito.fi)

    @staticmethod
    def nucleo_homogeneizado(composito, gsc=None) -> FaseMecanica:
        """A inclusão homogeneizada com o revestimento (primeiro passo, fração fi / (fi + fr))."""
        fi, fr = composito.fi, composito.fr
        if fr == 0:
            return composito.inclusao
        if fi == 0:
            return composito.revestimento
        interno = (gsc or GSC()).homogeneizar(
            Composito(composito.revestimento, composito.inclusao, fi / (fi + fr)))
        return FaseMecanica(interno.Eh, interno.vh)
