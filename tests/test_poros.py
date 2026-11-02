"""Poros: fase sem rigidez (E = 0) criada só por FaseMecanica.poro()."""
from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from hoop.homogenizacao.composito import Composito, CompositoRevestido
from hoop.materiais.fases import FaseMecanica
from hoop.micmodelos.dilute import DiluteSuspension
from hoop.micmodelos.gsc import GSC
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.popovic import Popovic
from hoop.micmodelos.reuss import Reuss
from hoop.micmodelos.selfconsistent import SelfConsistent
from hoop.micmodelos.voigt import Voigt

MATRIZ = FaseMecanica(30.0, 0.2)   # GPa
PORO = FaseMecanica.poro()


def modulos(fase):
    return fase.E / (3 * (1 - 2 * fase.v)), fase.E / (2 * (1 + fase.v))


def mori_tanaka_com_vazio(fase, f):
    """Fórmulas fechadas de Mori-Tanaka para vazios esféricos."""
    K, G = modulos(fase)
    Kh = 4 * G * K * (1 - f) / (4 * G + 3 * K * f)
    Gh = G * (1 - f) / (1 + f * (6 * K + 12 * G) / (9 * K + 8 * G))
    return Kh, Gh


# --- criação -----------------------------------------------------------------

def test_poro_tem_rigidez_nula_e_e_imutavel():
    assert PORO.E == 0 and PORO.vazio
    np.testing.assert_array_equal(PORO.L, np.zeros((6, 6)))
    with pytest.raises(FrozenInstanceError):
        PORO.E = 1.0


@pytest.mark.parametrize('E', [0, 0.0])
def test_fase_comum_com_E_zero_continua_proibida(E):
    with pytest.raises(ValueError, match='poro'):
        FaseMecanica(E, 0.2)


def test_poro_exige_E_zero_e_poisson_valido():
    with pytest.raises(ValueError, match='E = 0'):
        FaseMecanica(10.0, 0.2, vazio=True)
    with pytest.raises(ValueError, match='Poisson'):
        FaseMecanica.poro(v=0.5)


def test_eshelby_do_poro_depende_so_de_poisson():
    np.testing.assert_allclose(PORO.eshelby('esfera'), FaseMecanica(7.0, 0.2).eshelby('esfera'),
                               atol=1e-14)


def test_poro_nao_tem_tensor_de_hill():
    with pytest.raises(ValueError, match='matriz'):
        PORO.P


def test_poro_nao_pode_ser_matriz():
    with pytest.raises(ValueError, match='matriz não pode ser um poro'):
        Composito(PORO, MATRIZ, fi=0.1)
    with pytest.raises(ValueError, match='matriz não pode ser um poro'):
        CompositoRevestido(PORO, MATRIZ, MATRIZ, fi=0.1, fr=0.1)


# --- modelos -----------------------------------------------------------------

@pytest.mark.parametrize('f', [0.0, 0.0242, 0.1, 0.3, 0.5])
def test_mori_tanaka_com_poros_segue_a_formula_fechada(f):
    r = MoriTanaka().homogeneizar(Composito(MATRIZ, PORO, f))
    Kh, Gh = mori_tanaka_com_vazio(MATRIZ, f)
    assert r.kh == pytest.approx(Kh) and r.Gh == pytest.approx(Gh)


@pytest.mark.parametrize('f', [0.05, 0.2, 0.4])
def test_dilute_e_self_consistent_com_poros_seguem_formulas_fechadas(f):
    """Com ν = 0,2 o Self-Consistent de vazios dá E = Em (1 - 2f), igual ao Dilute."""
    for Modelo in (DiluteSuspension, SelfConsistent):
        r = Modelo().homogeneizar(Composito(MATRIZ, PORO, f))
        assert r.Eh == pytest.approx(MATRIZ.E * (1 - 2 * f), rel=1e-6)


def test_voigt_com_poros_reduz_a_rigidez_pela_fracao_solida():
    r = Voigt().homogeneizar(Composito(MATRIZ, PORO, 0.25))
    assert r.Eh == pytest.approx(0.75 * MATRIZ.E)


def test_gsc_com_poros_coincide_com_poro_quase_sem_rigidez():
    exato = GSC().homogeneizar(Composito(MATRIZ, PORO, 0.1))
    quase = GSC().homogeneizar(Composito(MATRIZ, FaseMecanica(1e-9, 0.2), 0.1))
    assert 0 < exato.Eh < MATRIZ.E
    assert exato.Eh == pytest.approx(quase.Eh, rel=1e-8)


@pytest.mark.parametrize('Modelo, nome', [(Reuss, 'Reuss'), (Popovic, 'Popovic')])
@pytest.mark.parametrize('f', [0.0, 0.1])
def test_modelos_degenerados_recusam_poros(Modelo, nome, f):
    with pytest.raises(ValueError, match=f'{nome} não se aplica a poros.*Mori-Tanaka'):
        Modelo().homogeneizar(Composito(MATRIZ, PORO, f))


# --- resultados fora do domínio viram erro, não NaN nem E negativo ------------

@pytest.mark.parametrize('f', [0.5, 0.6, 0.95])
def test_dilute_com_poros_recusa_E_nao_positivo(f):
    with pytest.raises(ValueError, match='E nulo ou negativo'):
        DiluteSuspension().homogeneizar(Composito(MATRIZ, PORO, f))


@pytest.mark.parametrize('f', [0.5, 0.7, 0.9])
def test_self_consistent_recusa_poros_acima_da_percolacao(f):
    with pytest.raises(ValueError, match='limiar de percolação'):
        SelfConsistent().homogeneizar(Composito(MATRIZ, PORO, f))


def test_composito_so_de_vazio_e_recusado():
    with pytest.raises(ValueError, match='só vazio'):
        Composito(MATRIZ, PORO, 1.0)
    with pytest.raises(ValueError, match='só vazio'):
        CompositoRevestido(MATRIZ, PORO, FaseMecanica(10, .3), 1.0, 0.0)
    assert Composito(MATRIZ, FaseMecanica(10, .3), 1.0).fi == 1.0


def test_tensor_nao_finito_vira_erro():
    from hoop.micmodelos.micmodelos import Micmodelos
    C = np.full((6, 6), np.nan)
    with pytest.raises(ValueError, match='não finito'):
        Micmodelos._resultado_do_tensor(Composito(MATRIZ, PORO, 0.3), C)
