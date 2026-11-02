import warnings

import numpy as np
import pytest
from scipy.optimize import fsolve

from hoop.exemplos import criar_analise, MATERIAIS
from hoop.micmodelos.voigt import Voigt
from hoop.micmodelos.reuss import Reuss
from hoop.micmodelos.dilute import DiluteSuspension
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.selfconsistent import SelfConsistent
from hoop.micmodelos.gsc import GSC
from hoop.micmodelos.popovic import Popovic


SISTEMAS = dict(MATERIAIS)
SISTEMAS['inclusao_macia'] = dict(Em=30_000, vm=0.20, Ei=3_000, vi=0.35)
SISTEMAS['inclusao_muito_macia'] = dict(Em=30_000, vm=0.20, Ei=300, vi=0.45)

FRACOES = np.linspace(0, 1, 21)


def calcular(modelo, mat, fi):
    h = criar_analise(**mat)
    h.modH = modelo
    h.analH.fi = fi
    h.calc()
    return h.modH


def sc_referencia(Em, vm, Ei, vi, fi):
    """Self-Consistent para esferas resolvido diretamente pelas equações implícitas de Hill."""
    Km, Gm = Em / (3 * (1 - 2 * vm)), Em / (2 * (1 + vm))
    Ki, Gi = Ei / (3 * (1 - 2 * vi)), Ei / (2 * (1 + vi))

    def residuo(x):
        K, G = x
        a = 3 * K / (3 * K + 4 * G)
        b = 6 * (K + 2 * G) / (5 * (3 * K + 4 * G))
        return [fi * (Ki - K) / (1 + a * (Ki - K) / K) + (1 - fi) * (Km - K) / (1 + a * (Km - K) / K),
                fi * (Gi - G) / (1 + b * (Gi - G) / G) + (1 - fi) * (Gm - G) / (1 + b * (Gm - G) / G)]

    K, G = fsolve(residuo, [fi * Ki + (1 - fi) * Km, fi * Gi + (1 - fi) * Gm], xtol=1e-12)
    return 9 * K * G / (3 * K + G)


@pytest.mark.parametrize('Modelo', [Voigt, Reuss, MoriTanaka, SelfConsistent, GSC, Popovic])
@pytest.mark.parametrize('nome', list(SISTEMAS))
def test_extremos_recuperam_as_fases(Modelo, nome):
    mat = SISTEMAS[nome]
    assert calcular(Modelo(), mat, 0.0).Eh == pytest.approx(mat['Em'], rel=1e-6)
    assert calcular(Modelo(), mat, 1.0).Eh == pytest.approx(mat['Ei'], rel=1e-6)


@pytest.mark.parametrize('Modelo', [MoriTanaka, SelfConsistent, GSC, Popovic])
@pytest.mark.parametrize('nome', list(SISTEMAS))
def test_entre_limites_de_reuss_e_voigt(Modelo, nome):
    mat = SISTEMAS[nome]
    for fi in FRACOES:
        inf, sup = sorted([calcular(Reuss(), mat, fi).Eh, calcular(Voigt(), mat, fi).Eh])
        Eh = calcular(Modelo(), mat, fi).Eh
        assert inf * (1 - 1e-9) <= Eh <= sup * (1 + 1e-9), (fi, inf, Eh, sup)


@pytest.mark.parametrize('nome', list(SISTEMAS))
def test_self_consistent_bate_com_solucao_de_referencia(nome):
    mat = SISTEMAS[nome]
    for fi in FRACOES:
        Eh = calcular(SelfConsistent(), mat, fi).Eh
        assert Eh == pytest.approx(sc_referencia(**mat, fi=fi), rel=1e-6), fi


def test_self_consistent_avisa_quando_nao_converge():
    modelo = SelfConsistent()
    modelo.max_iter = 1
    with pytest.raises(RuntimeError, match='não convergiu'):
        calcular(modelo, SISTEMAS['epoxy_vidro'], 0.5)


def test_dilute_coincide_com_mori_tanaka_em_baixa_fracao():
    mat = SISTEMAS['concreto']
    dilute = calcular(DiluteSuspension(), mat, 0.01).Eh
    mt = calcular(MoriTanaka(), mat, 0.01).Eh
    assert dilute == pytest.approx(mt, rel=1e-3)


def test_popovic_e_media_de_voigt_e_reuss_sem_divisao_por_zero():
    mat = SISTEMAS['epoxy_vidro']
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        C = calcular(Popovic(), mat, 0.4).C
    Cv = calcular(Voigt(), mat, 0.4).C
    Cr = calcular(Reuss(), mat, 0.4).C
    np.testing.assert_allclose(C, (Cv + Cr) / 2)


@pytest.mark.parametrize('Modelo', [Voigt, MoriTanaka])
def test_tipo_de_analise_desconhecido_gera_value_error(Modelo):
    h = criar_analise(**SISTEMAS['concreto'])
    h.analH.analise_type = 'inexistente'
    h.modH = Modelo()
    with pytest.raises(ValueError, match='não suportado'):
        h.calc()
