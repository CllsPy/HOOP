import numpy as np
import pytest

from hoop.analise.analise import Analise
from hoop.exemplos import criar_analise, MATERIAIS
from hoop.homogenizacao.homogenizacao import Homogenizacao
from hoop.materiais.condutividade import Condutividade
from hoop.mecanico.mecanico import Mecanico
from hoop.mecanico.tensores import (propriedades_isotropicas, tensor_hill_esfera,
                                    tensor_rigidez_isotropico)
from hoop.micmodelos.dilute import DiluteSuspension
from hoop.micmodelos.gsc import GSC
from hoop.micmodelos.micmodelos import Micmodelos
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.popovic import Popovic
from hoop.micmodelos.protocolos import ModeloMecanico
from hoop.micmodelos.reuss import Reuss
from hoop.micmodelos.selfconsistent import SelfConsistent
from hoop.micmodelos.voigt import Voigt
from hoop.resultados.resultados import ResultadoMecanico

MODELOS = [Voigt, Reuss, MoriTanaka, GSC, Popovic, SelfConsistent, DiluteSuspension]
E_ACO, V_ACO = 210_000, 0.30


def criar_condutividade(km, ki, fi):
    h = Homogenizacao()
    h.tipo = 'global'
    h.analise_tipo = 'condutividade'
    h.geo = 'esfera'
    h.fi = fi
    h.set_analise()
    for k in (km, ki):
        mat = Condutividade()
        mat.k11 = mat.k22 = mat.k33 = k
        h.matH.append(mat)
    return h


# --- tensores puros -------------------------------------------------------

def test_tensor_rigidez_do_aco_tem_lame_conhecido():
    L = tensor_rigidez_isotropico(E_ACO, V_ACO)
    lame = E_ACO * V_ACO / ((1 + V_ACO) * (1 - 2 * V_ACO))
    G = E_ACO / (2 * (1 + V_ACO))
    assert L.shape == (6, 6)
    np.testing.assert_allclose(L, L.T)
    assert L[0, 1] == pytest.approx(lame)
    assert L[0, 0] == pytest.approx(lame + 2 * G)
    assert L[3, 3] == pytest.approx(G)


def test_propriedades_isotropicas_ida_e_volta():
    E, v, K, G = propriedades_isotropicas(tensor_rigidez_isotropico(E_ACO, V_ACO))
    assert E == pytest.approx(E_ACO)
    assert v == pytest.approx(V_ACO)
    assert K == pytest.approx(E_ACO / (3 * (1 - 2 * V_ACO)))
    assert G == pytest.approx(E_ACO / (2 * (1 + V_ACO)))


@pytest.mark.parametrize('indices', [(0, 1), (2, 1), (1, 2)])
def test_propriedades_isotropicas_independem_do_plano_para_tensor_isotropico(indices):
    L = tensor_rigidez_isotropico(E_ACO, V_ACO)
    assert propriedades_isotropicas(L, indices) == pytest.approx(propriedades_isotropicas(L))


def test_tensor_hill_esfera_gera_eshelby_classico():
    E, v = 1000, 0.25
    S = tensor_hill_esfera(E, v) @ tensor_rigidez_isotropico(E, v)
    assert S[0, 0] == pytest.approx((7 - 5 * v) / (15 * (1 - v)))
    assert S[0, 1] == pytest.approx((5 * v - 1) / (15 * (1 - v)))
    assert S[3, 3] == pytest.approx(2 * (4 - 5 * v) / (15 * (1 - v)))


def test_mecanico_delega_para_funcoes_puras_sem_efeito_colateral():
    m = Mecanico()
    m.E, m.v, m.geo = E_ACO, V_ACO, 'esfera'
    m.calc()
    np.testing.assert_array_equal(m.L, tensor_rigidez_isotropico(E_ACO, V_ACO))
    np.testing.assert_array_equal(m.P, tensor_hill_esfera(E_ACO, V_ACO))
    np.testing.assert_array_equal(Mecanico.montaL(E_ACO, V_ACO), m.L)

    P_antes = m.P.copy()
    S = m.montaS(1000, 0.25)
    np.testing.assert_array_equal(m.P, P_antes)
    np.testing.assert_allclose(S, tensor_hill_esfera(1000, 0.25) @ tensor_rigidez_isotropico(1000, 0.25))


def test_analise_guarda_parametros():
    a = Analise('mecanica', 'esfera', 0.2, 0.8, None)
    assert (a.analise_type, a.geo, a.fi, a.fm, a.fr) == ('mecanica', 'esfera', 0.2, 0.8, None)


# --- despacho por tipo de análise -----------------------------------------

@pytest.mark.parametrize('Modelo', MODELOS)
def test_despacho_mecanico(Modelo):
    mat = MATERIAIS['concreto']
    h = criar_analise(**mat)
    h.modH = Modelo()
    h.analH.fi = 0.3
    h.calc()
    m = h.modH
    assert mat['Em'] < m.Eh < mat['Ei']
    assert (m.Eh, m.vh, m.kh, m.Gh) == pytest.approx(propriedades_isotropicas(m.C))
    assert m.Em == mat['Em'] and m.Ei == mat['Ei'] and m.fi == 0.3


@pytest.mark.parametrize('Modelo', MODELOS)
def test_despacho_condutividade(Modelo):
    km, ki = 1.0, 20.0
    for fi, esperado in [(0.0, km), (1.0, ki)]:
        h = criar_condutividade(km, ki, fi)
        h.modH = Modelo()
        h.calc()
        if Modelo is not DiluteSuspension:  # diluída só vale para fi pequeno
            assert h.modH.K11 == pytest.approx(esperado)

    h = criar_condutividade(km, ki, 0.3)
    h.modH = Modelo()
    h.calc()
    m = h.modH
    assert km < m.K11 < ki
    assert m.K11 == pytest.approx(m.K22) == pytest.approx(m.K33)
    assert m.get_resultado_condutividade().K11 == m.K11


def test_self_consistent_condutividade_bate_com_formula_fechada():
    km, ki, fi = 1.0, 20.0, 0.3
    h = criar_condutividade(km, ki, fi)
    h.modH = SelfConsistent()
    h.calc()
    k = h.modH.K11
    # equação implícita do Self-Consistent para esferas
    residuo = fi * (ki - k) / (ki + 2 * k) + (1 - fi) * (km - k) / (km + 2 * k)
    assert residuo == pytest.approx(0, abs=1e-12)


@pytest.mark.parametrize('tipo', ['inexistente', 'dosagem', 'dosage', 'termomechanics'])
@pytest.mark.parametrize('Modelo', MODELOS)
def test_tipo_desconhecido_nao_suportado(Modelo, tipo):
    h = criar_analise(**MATERIAIS['concreto'])
    h.analH.analise_type = tipo
    h.modH = Modelo()
    with pytest.raises(ValueError, match='não suportado'):
        h.calc()


def test_modelo_sem_mixin_de_condutividade_nao_suporta_condutividade():
    class SoMecanico(Micmodelos, ModeloMecanico):
        def homogeneizar(self, composito):
            return ResultadoMecanico(Eh=1.0)

    h = criar_condutividade(1.0, 2.0, 0.5)
    h.modH = SoMecanico()
    with pytest.raises(ValueError, match='não suportado'):
        h.calc()

    h = criar_analise(**MATERIAIS['concreto'])
    h.modH = SoMecanico()
    h.calc()
    assert h.modH.Eh == 1.0


def test_self_consistent_parametros_configuraveis():
    modelo = SelfConsistent()
    modelo.tol = 1e-3
    h = criar_analise(**MATERIAIS['epoxy_vidro'])
    h.modH = modelo
    h.analH.fi = 0.4
    h.calc()
    preciso = criar_analise(**MATERIAIS['epoxy_vidro'])
    preciso.modH = SelfConsistent()
    preciso.analH.fi = 0.4
    preciso.calc()
    assert modelo.Eh == pytest.approx(preciso.modH.Eh, rel=1e-2)
