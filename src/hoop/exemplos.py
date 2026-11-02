"""
Sistemas de materiais de referência e fábrica de análises prontas para desenhar.

Uso:
    from hoop.exemplos import criar_analise, MATERIAIS

    h = criar_analise(**MATERIAIS['epoxy_vidro'])
"""
from hoop.homogenizacao.homogenizacao import Homogenizacao
from hoop.mecanico.mecanico import Mecanico


# ---------------------------------------------------------------------------
# Sistemas de materiais pré-definidos (E em MPa)
# ---------------------------------------------------------------------------
MATERIAIS = {
    # Concreto: matriz cimentícia + agregado graúdo
    'concreto': dict(Em=30_000, vm=0.20, Ei=70_000, vi=0.30),

    # Polímero reforçado com fibra de vidro (GFRP)
    'epoxy_vidro': dict(Em=3_500, vm=0.38, Ei=73_000, vi=0.22),

    # Aço + carboneto de tungstênio (metal-cerâmica)
    'aco_carbeto': dict(Em=210_000, vm=0.30, Ei=450_000, vi=0.24),

    # Baixo contraste: alumínio + inclusão rígida leve
    'baixo_contraste': dict(Em=70_000, vm=0.33, Ei=80_000, vi=0.30),

    # Alto contraste: epóxi + fibra de carbono (HM)
    'epoxy_carbono': dict(Em=3_500, vm=0.38, Ei=390_000, vi=0.20),

    # Polímero + esferas de aço (alta razão de rigidez)
    'polimero_aco': dict(Em=3_000, vm=0.35, Ei=210_000, vi=0.30),
}


def criar_analise(Em: float, vm: float,
                  Ei: float, vi: float,
                  geo: str = 'esfera',
                  fi: float = 0.0,
                  analise_tipo: str = 'mecanica') -> Homogenizacao:
    """
    Factory: cria e configura um objeto Homogenizacao pronto para d.desenha().

    Args:
        Em:           Módulo de Young da matriz [MPa]
        vm:           Coeficiente de Poisson da matriz
        Ei:           Módulo de Young da inclusão [MPa]
        vi:           Coeficiente de Poisson da inclusão
        geo:          Geometria da inclusão ('esfera', 'cilindro', 'disco')
        fi:           fi máximo simulado — 0 usa range completo 0→1
        analise_tipo: 'mecanica' ou 'condutividade'

    Returns:
        Homogenizacao configurada com matH = [matriz, inclusão]
    """
    h = Homogenizacao()
    h.tipo         = 'global'
    h.analise_tipo = analise_tipo
    h.geo          = geo
    h.Em, h.vm     = Em, vm
    h.Ei, h.vi     = Ei, vi
    h.fi           = fi
    h.set_analise()

    m1 = Mecanico(); m1.E = Em; m1.v = vm; m1.geo = geo
    m2 = Mecanico(); m2.E = Ei; m2.v = vi; m2.geo = geo
    h.matH.extend([m1, m2])
    return h
