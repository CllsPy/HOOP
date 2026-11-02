"""Núcleo imutável: fases, Composito e a API sem estado dos modelos."""
from dataclasses import FrozenInstanceError, replace

import numpy as np
import pytest

from hoop.exemplos import MATERIAIS, criar_analise
from hoop.homogenizacao.composito import Composito
from hoop.homogenizacao.homogenizacao import Homogenizacao
from hoop.materiais.condutividade import Condutividade
from hoop.materiais.fases import FaseCondutividade, FaseMecanica
from hoop.mecanico.geometria_registry import tensor_eshelby
from hoop.mecanico.mecanico import Mecanico
from hoop.mecanico.tensores import tensor_hill_esfera, tensor_rigidez_isotropico
from hoop.micmodelos.dilute import DiluteSuspension
from hoop.micmodelos.gsc import GSC
from hoop.micmodelos.micmodelos import homogeneizar
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.popovic import Popovic
from hoop.micmodelos.reuss import Reuss
from hoop.micmodelos.selfconsistent import SelfConsistent
from hoop.micmodelos.voigt import Voigt
from hoop.resultados.resultados import ResultadoCondutividade, ResultadoMecanico

MODELOS = [Voigt, Reuss, DiluteSuspension, MoriTanaka, SelfConsistent, GSC, Popovic]
FRACOES = [0.0, 0.3, 1.0]
CONCRETO = MATERIAIS['concreto']


def composito_de(mat, fi=0.0, geometria='esfera'):
    return Composito(FaseMecanica(mat['Em'], mat['vm']), FaseMecanica(mat['Ei'], mat['vi']),
                     fi=fi, geometria=geometria)


def composito_condutividade(km=1.0, ki=20.0, fi=0.0):
    return Composito(FaseCondutividade.isotropica(km), FaseCondutividade.isotropica(ki), fi=fi)


def analise_condutividade(km, ki, fi):
    h = Homogenizacao()
    h.tipo, h.analise_tipo, h.geo = 'global', 'condutividade', 'esfera'
    h.set_analise()
    h.analH.fi = fi
    for k in (km, ki):
        c = Condutividade()
        c.k11 = c.k22 = c.k33 = k
        h.matH.append(c)
    return h


# --- imutabilidade ----------------------------------------------------------

@pytest.mark.parametrize('objeto, campo, valor', [
    (FaseMecanica(30_000, 0.2), 'E', 1.0),
    (FaseMecanica(30_000, 0.2), 'v', 0.3),
    (FaseCondutividade(1.0, 2.0, 3.0), 'k11', 5.0),
    (composito_de(CONCRETO), 'fi', 0.5),
    (composito_de(CONCRETO), 'matriz', FaseMecanica(1.0, 0.1)),
    (composito_de(CONCRETO), 'geometria', 'disco'),
])
def test_objetos_de_valor_sao_congelados(objeto, campo, valor):
    with pytest.raises(FrozenInstanceError):
        setattr(objeto, campo, valor)


@pytest.mark.parametrize('tensor', [
    lambda: FaseMecanica(30_000, 0.2).L,
    lambda: FaseMecanica(30_000, 0.2).P,
    lambda: FaseMecanica(30_000, 0.2).eshelby('esfera'),
    lambda: FaseCondutividade(1.0, 2.0, 3.0).K,
    lambda: composito_de(CONCRETO).eshelby,
])
def test_tensores_derivados_sao_somente_leitura(tensor):
    with pytest.raises(ValueError, match='read-only'):
        tensor()[0, 0] = 0.0


def test_tensores_derivados_reutilizam_as_funcoes_puras():
    fase = FaseMecanica(30_000, 0.2)
    np.testing.assert_array_equal(fase.L, tensor_rigidez_isotropico(30_000, 0.2))
    np.testing.assert_array_equal(fase.P, tensor_hill_esfera(30_000, 0.2))
    np.testing.assert_array_equal(fase.eshelby('cilindro'), tensor_eshelby('cilindro', 30_000, 0.2))
    assert fase.L is fase.L  # calculado uma vez
    np.testing.assert_array_equal(FaseCondutividade(1.0, 2.0, 3.0).K, np.diag([1.0, 2.0, 3.0]))


def test_replace_cria_outro_composito_sem_alterar_o_original():
    base = composito_de(CONCRETO, fi=0.3)
    outro = replace(base, fi=0.6)
    assert (base.fi, outro.fi) == (0.3, 0.6)
    assert outro.matriz is base.matriz and outro == base.com_fracao(0.6)
    assert outro.fm == pytest.approx(0.4)


def test_composito_e_igual_por_valor_e_hashable():
    assert composito_de(CONCRETO, 0.3) == composito_de(CONCRETO, 0.3)
    assert len({composito_de(CONCRETO, 0.3), composito_de(CONCRETO, 0.3)}) == 1


# --- validação ao nascer ----------------------------------------------------

@pytest.mark.parametrize('E, v', [
    (0, 0.2), (-1.0, 0.2), (float('nan'), 0.2), (float('inf'), 0.2), ('30000', 0.2), (True, 0.2),
    (30_000, 0.5), (30_000, -1.0), (30_000, 0.7), (30_000, float('nan')), (30_000, None),
])
def test_fase_mecanica_rejeita_valores_fora_da_faixa(E, v):
    with pytest.raises(ValueError, match='E|v'):
        FaseMecanica(E, v)


@pytest.mark.parametrize('k', [(0.0, 1.0, 1.0), (1.0, -2.0, 1.0), (1.0, 1.0, float('nan'))])
def test_fase_condutividade_rejeita_valores_nao_positivos(k):
    with pytest.raises(ValueError, match='k'):
        FaseCondutividade(*k)


@pytest.mark.parametrize('fi', [-0.01, 1.01, float('nan'), None, '0.3', True])
def test_composito_rejeita_fracao_fora_de_0_a_1(fi):
    with pytest.raises(ValueError, match='fi'):
        composito_de(CONCRETO, fi=fi)


def test_replace_tambem_valida():
    with pytest.raises(ValueError, match='fi'):
        replace(composito_de(CONCRETO), fi=2.0)


def test_composito_rejeita_geometria_desconhecida():
    with pytest.raises(ValueError, match="'elipse' não registrada"):
        composito_de(CONCRETO, geometria='elipse')


def test_composito_rejeita_fases_de_tipos_diferentes():
    with pytest.raises(ValueError, match='mesmo tipo'):
        Composito(FaseMecanica(30_000, 0.2), FaseCondutividade.isotropica(1.0), fi=0.3)
    with pytest.raises(ValueError, match='matriz'):
        Composito(Mecanico(), FaseMecanica(30_000, 0.2), fi=0.3)


def test_composito_informa_o_tipo_de_analise():
    assert composito_de(CONCRETO).analise == 'mecanica'
    assert composito_condutividade().analise == 'condutividade'


def test_condutividade_fora_da_esfera_falha_ao_pedir_eshelby():
    c = Composito(FaseCondutividade.isotropica(1.0), FaseCondutividade.isotropica(2.0),
                  fi=0.3, geometria='cilindro')
    with pytest.raises(NotImplementedError, match='cilindro'):
        MoriTanaka().homogeneizar_condutividade(c)


@pytest.mark.parametrize('fi', FRACOES)
def test_mori_tanaka_com_fases_iguais_devolve_a_matriz(fi):
    fase = FaseMecanica(30_000, 0.2)
    resultado = MoriTanaka().homogeneizar(Composito(fase, fase, fi=fi))
    assert resultado.Eh == pytest.approx(30_000) and resultado.vh == pytest.approx(0.2)
    cond = MoriTanaka().homogeneizar_condutividade(composito_condutividade(2.0, 2.0, fi))
    assert cond.K11 == pytest.approx(2.0)


def test_mori_tanaka_com_mesmo_cisalhamento_segue_hashin_shtrikman():
    """Gm = Gi = 12 500: só o volumétrico muda, e MT coincide com a fórmula fechada."""
    km, ki, g, fi = 30_000 / 1.8, 32_500 / 1.2, 12_500, 0.3
    c = Composito(FaseMecanica(30_000, 0.2), FaseMecanica(32_500, 0.3), fi=fi)
    esperado = km + fi * (ki - km) / (1 + (1 - fi) * (ki - km) / (km + 4 / 3 * g))
    resultado = MoriTanaka().homogeneizar(c)
    assert resultado.kh == pytest.approx(esperado)
    assert resultado.Gh == pytest.approx(g)


# --- equivalência exata entre a API nova e o adaptador antigo ---------------

def mesmos_valores(a, b):
    return all(np.array_equal(x, y) if isinstance(x, np.ndarray) else x == y
               for x, y in zip(a, b))


@pytest.mark.parametrize('fi', FRACOES)
@pytest.mark.parametrize('nome', list(MATERIAIS))
@pytest.mark.parametrize('Modelo', MODELOS)
def test_api_nova_e_adaptador_dao_resultados_identicos(Modelo, nome, fi):
    mat = MATERIAIS[nome]
    resultado = Modelo().homogeneizar(composito_de(mat, fi))

    h = criar_analise(**mat)
    h.modH = Modelo()
    h.analH.fi = fi
    h.calc()
    m = h.modH

    assert isinstance(resultado, ResultadoMecanico)
    assert mesmos_valores((resultado.Eh, resultado.vh, resultado.kh, resultado.Gh),
                          (m.Eh, m.vh, m.kh, m.Gh))
    assert np.array_equal(resultado.C, m.C)
    assert (resultado.Em, resultado.fi) == (mat['Em'], fi) == (m.Em, m.fi)


@pytest.mark.parametrize('fi', FRACOES)
@pytest.mark.parametrize('Modelo', MODELOS)
def test_condutividade_api_nova_e_adaptador_identicos(Modelo, fi):
    resultado = Modelo().homogeneizar_condutividade(composito_condutividade(1.0, 20.0, fi))
    h = analise_condutividade(1.0, 20.0, fi)
    h.modH = Modelo()
    h.calc()

    assert isinstance(resultado, ResultadoCondutividade)
    assert np.array_equal(resultado.kh, h.modH.kh)
    assert (resultado.K11, resultado.K22, resultado.K33) == (h.modH.K11, h.modH.K22, h.modH.K33)


@pytest.mark.parametrize('geometria', ['cilindro', 'disco'])
@pytest.mark.parametrize('Modelo', [MoriTanaka, DiluteSuspension])
def test_equivalencia_vale_para_outras_geometrias(Modelo, geometria):
    resultado = Modelo().homogeneizar(composito_de(CONCRETO, 0.3, geometria))
    h = criar_analise(**CONCRETO, geo=geometria)
    h.modH = Modelo()
    h.analH.fi = 0.3
    h.calc()
    assert np.array_equal(resultado.C, h.modH.C)


def test_homogenizacao_expoe_o_composito_equivalente():
    h = criar_analise(**CONCRETO)
    h.analH.fi = 0.3
    assert h.composito() == composito_de(CONCRETO, 0.3)


def test_homogenizacao_sem_modelo_gera_erro_claro():
    h = criar_analise(**CONCRETO)
    with pytest.raises(ValueError, match='modH'):
        h.calc()


def test_homogeneizar_despacha_pelo_tipo_das_fases():
    assert isinstance(homogeneizar(Voigt(), composito_de(CONCRETO, 0.3)), ResultadoMecanico)
    assert isinstance(homogeneizar(Voigt(), composito_condutividade(fi=0.3)), ResultadoCondutividade)


# --- ausência de efeitos colaterais -----------------------------------------

@pytest.mark.parametrize('Modelo', MODELOS)
def test_homogeneizar_nao_altera_modelo_nem_composito(Modelo):
    modelo = Modelo()
    composito = composito_de(MATERIAIS['epoxy_vidro'], 0.3)
    copia = composito_de(MATERIAIS['epoxy_vidro'], 0.3)
    estado_antes = dict(vars(modelo))
    L_matriz = composito.matriz.L.copy()

    primeiro = modelo.homogeneizar(composito)
    segundo = modelo.homogeneizar(composito)

    assert vars(modelo) == estado_antes
    assert composito == copia
    np.testing.assert_array_equal(composito.matriz.L, L_matriz)
    assert np.array_equal(primeiro.C, segundo.C) and primeiro.Eh == segundo.Eh


@pytest.mark.parametrize('Modelo', MODELOS)
def test_homogeneizar_condutividade_nao_altera_o_modelo(Modelo):
    modelo = Modelo()
    estado_antes = dict(vars(modelo))
    modelo.homogeneizar_condutividade(composito_condutividade(fi=0.3))
    assert vars(modelo) == estado_antes


def test_um_modelo_serve_compositos_diferentes_sem_interferencia():
    modelo = MoriTanaka()
    a, b = composito_de(CONCRETO, 0.2), composito_de(MATERIAIS['epoxy_vidro'], 0.4)
    ra = modelo.homogeneizar(a)
    modelo.homogeneizar(b)
    assert np.array_equal(modelo.homogeneizar(a).C, ra.C)


def test_resultados_sao_congelados():
    r = Voigt().homogeneizar(composito_de(CONCRETO, 0.3))
    with pytest.raises(FrozenInstanceError):
        r.Eh = 0.0


def test_fases_antigas_convertem_para_objetos_de_valor():
    m = Mecanico()
    m.E, m.v = 30_000, 0.2
    assert m.como_fase() == FaseMecanica(30_000, 0.2)
    c = Condutividade()
    c.k11, c.k22, c.k33 = 1.0, 2.0, 3.0
    assert c.como_fase() == FaseCondutividade(1.0, 2.0, 3.0)
