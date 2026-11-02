"""Compósito revestido, modelos de três fases e o concreto multiescala (tese, seção 3.1).

Referências: Silva (2022), Tabelas 3 a 8. Módulos em GPa.
"""
from dataclasses import FrozenInstanceError, replace

import numpy as np
import pytest

from hoop.homogenizacao.composito import Composito, CompositoRevestido
from hoop.homogenizacao.multiescala import (Constituinte, FasesConcreto, ResultadoMultiescala,
                                            calcular_concreto)
from hoop.materiais.fases import FaseCondutividade, FaseMecanica
from hoop.micmodelos.gsc import GSC
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.multiplasfases import MultiplasFases
from hoop.micmodelos.quatrofases import QuatroFases
from hoop.micmodelos.reuss import Reuss

PASTA = FaseMecanica(21.34, 0.25)
MIUDO = FaseMecanica(77.60, 0.15)
ZTI2 = FaseMecanica(12.70, 0.25)
LI_2019 = FasesConcreto.li_2019()


def modulos_E(resultado: ResultadoMultiescala):
    return [n.resultado.Eh for n in resultado.niveis]


# --- CompositoRevestido -------------------------------------------------------

def test_composito_revestido_e_imutavel_e_calcula_fm():
    c = CompositoRevestido(PASTA, MIUDO, ZTI2, fi=0.4686, fr=0.2631)
    assert c.fm == pytest.approx(0.2683)
    assert c.analise == 'mecanica'
    with pytest.raises(FrozenInstanceError):
        c.fi = 0.1


@pytest.mark.parametrize('fi, fr', [(-0.1, 0.2), (0.2, -0.1), (0.7, 0.4), (float('nan'), 0.1),
                                    (0.2, None)])
def test_composito_revestido_rejeita_fracoes_invalidas(fi, fr):
    with pytest.raises(ValueError, match='fi|fr'):
        CompositoRevestido(PASTA, MIUDO, ZTI2, fi=fi, fr=fr)


def test_composito_revestido_exige_fases_mecanicas():
    with pytest.raises(ValueError, match='revestimento deve ser FaseMecanica'):
        CompositoRevestido(PASTA, MIUDO, FaseCondutividade.isotropica(1.0), fi=0.3, fr=0.1)


def test_replace_do_composito_revestido_valida_de_novo():
    c = CompositoRevestido(PASTA, MIUDO, ZTI2, fi=0.4, fr=0.2)
    with pytest.raises(ValueError, match='fi \\+ fr'):
        replace(c, fr=0.7)


# --- Quatro-Fases e Múltiplas-Fases: casos-limite ----------------------------

@pytest.mark.parametrize('fi, fr', [(0.3, 0.0), (0.0, 0.3), (0.2, 0.2)])
def test_quatro_fases_reduz_ao_gsc_nos_casos_limite(fi, fr):
    """Sem revestimento é o GSC da inclusão; sem inclusão, o GSC do revestimento;
    com revestimento igual à inclusão, o GSC com fi + fr."""
    revestimento = MIUDO if fi and fr else ZTI2
    r = QuatroFases().homogeneizar(CompositoRevestido(PASTA, MIUDO, revestimento, fi, fr))
    nucleo = MIUDO if fi else ZTI2
    esperado = GSC().homogeneizar(Composito(PASTA, nucleo, fi + fr))
    assert r.Eh == pytest.approx(esperado.Eh, rel=1e-9)
    assert r.fi == fi


def test_quatro_fases_usa_fracao_corrigida_no_primeiro_passo():
    """Eq. 146: o núcleo é GSC(revestimento + inclusão) com fi / (fi + fr) (o legado usava fi)."""
    c = CompositoRevestido(PASTA, MIUDO, ZTI2, fi=0.4686, fr=0.2631)
    nucleo = QuatroFases.nucleo_homogeneizado(c)
    esperado = GSC().homogeneizar(Composito(ZTI2, MIUDO, 0.4686 / (0.4686 + 0.2631)))
    assert nucleo.E == pytest.approx(esperado.Eh)


def test_multiplas_fases_com_revestimento_igual_a_inclusao_e_mori_tanaka():
    """Ci = Cr anula ΔS e o modelo cai no Mori-Tanaka com fração fi + fr.

    Vale quando a inclusão tem o ν da matriz: o Multi-Fases monta o Eshelby
    com o ν da própria inclusão, o Mori-Tanaka com o da matriz.
    """
    inclusao = FaseMecanica(77.60, PASTA.v)
    r = MultiplasFases().homogeneizar(CompositoRevestido(PASTA, inclusao, inclusao, 0.3, 0.1))
    esperado = MoriTanaka().homogeneizar(Composito(PASTA, inclusao, 0.4))
    np.testing.assert_allclose(r.C, esperado.C, rtol=1e-9)


def test_multiplas_fases_sem_inclusao_nem_revestimento_devolve_a_matriz():
    r = MultiplasFases().homogeneizar(CompositoRevestido(PASTA, MIUDO, ZTI2, 0.0, 0.0))
    assert r.Eh == pytest.approx(PASTA.E) and r.vh == pytest.approx(PASTA.v)


def test_multiplas_fases_exige_inclusao():
    with pytest.raises(ValueError, match='fr / fi = infinita'):
        MultiplasFases().homogeneizar(CompositoRevestido(PASTA, MIUDO, ZTI2, 0.0, 0.2))


@pytest.mark.parametrize('fi', [1e-9, 1e-3, 0.05, 0.099])
def test_multiplas_fases_recusa_revestimento_maior_que_a_inclusao(fi):
    """fr / fi grande é singular: com fi = 1e-9 o modelo dava 25,13 > Voigt (19,0)."""
    c = CompositoRevestido(FaseMecanica(20, .25), FaseMecanica(70, .15), FaseMecanica(10, .3),
                           fi, 0.1)
    with pytest.raises(ValueError, match='Quatro fases'):
        MultiplasFases().homogeneizar(c)


@pytest.mark.parametrize('fr', [0.02, 0.1, 0.26])
def test_multiplas_fases_cresce_com_fi_e_fica_entre_reuss_e_voigt_no_dominio(fr):
    """Com fr / fi <= 1 a curva E(fi) é monotônica e respeita os limites das três fases."""
    M, I, R = FaseMecanica(20, .25), FaseMecanica(70, .15), FaseMecanica(10, .3)
    fis = np.linspace(fr, 0.6, 60)
    E = np.array([MultiplasFases().homogeneizar(CompositoRevestido(M, I, R, fi, fr)).Eh
                  for fi in fis])
    voigt = (1 - fis - fr) * M.E + fis * I.E + fr * R.E
    reuss = 1 / ((1 - fis - fr) / M.E + fis / I.E + fr / R.E)
    assert np.all(np.diff(E) > 0)
    assert np.all(E <= voigt) and np.all(E >= reuss)


def test_multiplas_fases_com_poro_usa_o_poisson_da_matriz():
    """O ν de um vazio não tem sentido físico: o resultado não pode depender dele."""
    resultados = [MultiplasFases().homogeneizar(
        CompositoRevestido(FaseMecanica(20, .25), FaseMecanica.poro(v), FaseMecanica(10, .3),
                           0.1, 0.05)) for v in (0.1, 0.2, 0.4)]
    for r in resultados[1:]:
        np.testing.assert_allclose(r.C, resultados[0].C, rtol=1e-12)


@pytest.mark.parametrize('papel', ['inclusao', 'revestimento'])
def test_multiplas_fases_recusa_fase_com_a_rigidez_da_matriz(papel):
    fases = {'inclusao': MIUDO, 'revestimento': ZTI2, papel: FaseMecanica(PASTA.E, PASTA.v)}
    with pytest.raises(ValueError, match=f'{papel} e matriz têm o mesmo módulo'):
        MultiplasFases().homogeneizar(CompositoRevestido(PASTA, fi=0.3, fr=0.1, **fases))


def test_multiplas_fases_aceita_inclusao_porosa():
    r = MultiplasFases().homogeneizar(
        CompositoRevestido(PASTA, FaseMecanica.poro(), ZTI2, 0.1, 0.05))
    assert 0 < r.Eh < PASTA.E


def test_quatro_fases_recusa_revestimento_poroso_e_outras_geometrias():
    with pytest.raises(ValueError, match='revestimento poroso'):
        QuatroFases().homogeneizar(CompositoRevestido(PASTA, MIUDO, FaseMecanica.poro(), 0.3, 0.1))
    with pytest.raises(ValueError, match='esfera'):
        QuatroFases().homogeneizar(
            CompositoRevestido(PASTA, MIUDO, ZTI2, 0.3, 0.1, geometria='cilindro'))


# --- FasesConcreto e frações por nível ---------------------------------------

def test_preset_li_2019_soma_100_por_cento_de_solidos():
    assert LI_2019.tem_zti and LI_2019.E_experimental == 34.50
    assert LI_2019.fracao_poros(com_zti=True) == pytest.approx(2.42 / 102.42)   # Tabela 7: 2,36%


def test_fracoes_por_nivel_com_zti_reproduzem_a_tabela_7():
    r = calcular_concreto(LI_2019, QuatroFases())
    n1, n2, n3 = r.niveis
    assert n1.fases == ('Pasta de cimento', 'Agregado miúdo', 'ZTI-2')
    np.testing.assert_allclose(n1.fracoes, (0.2683, 0.4686, 0.2631), atol=5e-5)
    np.testing.assert_allclose(n2.fracoes, (0.574, 0.403, 0.023), atol=1e-12)
    np.testing.assert_allclose(n3.fracoes, (0.9764, 0.0236), atol=5e-5)


def test_fracoes_por_nivel_sem_zti_reproduzem_a_tabela_4():
    """A Tabela 4 troca os rótulos do nível 2: o graúdo é 40,3 / 82,6 = 48,79%.

    No nível 3 ela imprime 2,78% de poros, mas os valores da Tabela 6 só são
    reproduzidos com a mesma regra da Tabela 7: 2,42 / (82,6 + 2,42) = 2,846%.
    """
    n1, n2, n3 = calcular_concreto(LI_2019, MoriTanaka(), com_zti=False).niveis
    np.testing.assert_allclose(n1.fracoes, (0.3641, 0.6359), atol=5e-5)
    assert n2.fracoes[1] == pytest.approx(40.3 / 82.6)
    assert n3.fracoes[1] == pytest.approx(2.42 / 85.02)


def test_fases_concreto_valida_soma_e_zti_em_par():
    with pytest.raises(ValueError, match='soma das frações sólidas'):
        replace(LI_2019, pasta=Constituinte(PASTA, 0.30))
    with pytest.raises(ValueError, match='duas ZTIs'):
        replace(LI_2019, zti_graudo=None)
    with pytest.raises(ValueError, match='poros'):
        replace(LI_2019, poros=2.42)
    with pytest.raises(ValueError, match='sólida'):
        Constituinte(FaseMecanica.poro(), 0.1)


def test_fases_concreto_exige_pasta():
    """Sem pasta o nível 1 não tem matriz (antes: ZeroDivisionError em calcular_concreto)."""
    zero = Constituinte(PASTA, 0.0)
    with pytest.raises(ValueError, match='pasta'):
        FasesConcreto(zero, Constituinte(MIUDO, 0.0), Constituinte(MIUDO, 0.9),
                      Constituinte(ZTI2, 0.0), Constituinte(ZTI2, 0.1))
    with pytest.raises(ValueError, match='pasta'):
        FasesConcreto(zero, Constituinte(MIUDO, 0.4), Constituinte(MIUDO, 0.6))


def test_concreto_sem_zti_dispensa_as_ztis():
    sem_zti = FasesConcreto(Constituinte(PASTA, 0.154 / 0.826), Constituinte(MIUDO, 0.269 / 0.826),
                            Constituinte(FaseMecanica(51.31, 0.15), 0.403 / 0.826), poros=0.0242)
    a = calcular_concreto(sem_zti, MoriTanaka(), com_zti=False)
    b = calcular_concreto(LI_2019, MoriTanaka(), com_zti=False)
    assert modulos_E(a)[:2] == pytest.approx(modulos_E(b)[:2])
    assert a.erro_relativo is None
    with pytest.raises(ValueError, match='com_zti=True exige'):
        calcular_concreto(sem_zti, QuatroFases())


def test_modelo_incompativel_com_a_construcao_gera_erro_claro():
    with pytest.raises(ValueError, match='três fases'):
        calcular_concreto(LI_2019, MoriTanaka(), com_zti=True)
    with pytest.raises(ValueError, match='duas fases'):
        calcular_concreto(LI_2019, QuatroFases(), com_zti=False)
    with pytest.raises(ValueError, match='Reuss não se aplica a poros'):
        calcular_concreto(LI_2019, QuatroFases(), modelo_poros=Reuss())


def test_sem_poros_ha_apenas_dois_niveis():
    r = calcular_concreto(replace(LI_2019, poros=0.0), QuatroFases())
    assert [n.nome for n in r.niveis] == ['Argamassa', 'Concreto']


# --- números da tese ----------------------------------------------------------

@pytest.mark.parametrize('Modelo, tese', [
    (MoriTanaka, (45.614, 48.341, 45.671)),
    (GSC, (46.144, 48.624, 45.937)),
])
def test_tabela_6_sem_zti(Modelo, tese):
    """Tabela 6 (sem ZTI), tolerância de 0,05% nos três níveis.

    O nível 3 só bate com 2,846% de poros (ver teste da Tabela 4); com os
    2,78% impressos na Tabela 4 daria MT 45,732 e GSC 46,000 (0,13%).
    Poros por Mori-Tanaka: GSC dá 45,939 (com o próprio GSC nos poros, 45,937).
    """
    r = calcular_concreto(LI_2019, Modelo(), com_zti=False)
    assert modulos_E(r) == pytest.approx(tese, rel=5e-4)


def test_tabela_6_gsc_com_gsc_nos_poros_reproduz_exatamente():
    r = calcular_concreto(LI_2019, GSC(), com_zti=False, modelo_poros=GSC())
    assert r.Eh == pytest.approx(45.937, rel=1e-4)


def test_tabela_8_quatro_fases():
    """Tabela 8: 30,638 / 36,167 / 34,501. Obtido: 30,785 / 36,321 / 34,645 (~0,47% acima).

    A formulação é a de Li et al. (1999) descrita nas Eqs. 146-148 (GSC do
    revestimento + inclusão com fi / (fi + fr), depois GSC com a matriz). Foram
    testadas sem sucesso outras combinações (MT, SC, Hashin-Shtrikman, Voigt e
    Reuss em cada passo; frações fi, fr, fr / (fi + fr); troca de papéis das
    fases; ν do núcleo): nenhuma reproduz os dois níveis ao mesmo tempo. O
    nível 1 da tese exigiria, por exemplo, E da pasta = 20,99 GPa. A razão
    nível 3 / nível 2 coincide (0,9539), então a diferença nasce no nível 1.
    """
    r = calcular_concreto(LI_2019, QuatroFases())
    assert modulos_E(r) == pytest.approx((30.638, 36.167, 34.501), rel=6e-3)
    assert abs(r.erro_relativo) < 0.01   # tese: 0,0031%; obtido: 0,42%


def test_tabela_8_multiplas_fases():
    """Tabela 8: 32,101 / 37,774 / 36,302. Obtido: 32,179 / 37,857 / 36,112.

    Eshelby da inclusão e do revestimento montados com o ν de cada fase, como
    no texto da tese e no m_phases.py do autor. Níveis 1 e 2 ficam ~0,24%
    acima; o nível 3 fica 0,52% abaixo, embora os poros usem o mesmo
    Mori-Tanaka que reproduz a Tabela 7 no Quatro-Fases (razão nível 3 /
    nível 2: tese 0,9610, obtido 0,9539), o que sugere outra fração de poros
    no nível 3 da tese para este modelo (~1,99% a partir do nível 2 da tese).
    Com o Eshelby montado com o ν da matriz nas duas fases (forma clássica)
    sairia 32,062 / 37,776 / 36,036.
    """
    r = calcular_concreto(LI_2019, MultiplasFases())
    E1, E2, E3 = modulos_E(r)
    assert (E1, E2) == pytest.approx((32.101, 37.774), rel=6e-3)
    assert E3 == pytest.approx(36.302, rel=7e-3)


def test_multiplas_fases_segue_o_codigo_do_autor_e_nao_as_equacoes_impressas():
    """Valores fixos da forma do m_phases.py (fr / fi em A_i^D, concentração normalizada).

    As Eqs. 150-157 impressas (fi / fr em A_r^D, Eq. 157 diluída) ficam mais
    longe da Tabela 8 (32,101 / 37,774 / 36,302); a diferença para a tabela
    fica registrada abaixo.
    """
    E = modulos_E(calcular_concreto(LI_2019, MultiplasFases()))
    assert E == pytest.approx((32.1788, 37.8574, 36.1122), rel=1e-5)
    diferenca = np.array(E) / np.array((32.101, 37.774, 36.302)) - 1
    np.testing.assert_allclose(diferenca, (0.0024, 0.0022, -0.0052), atol=2e-4)
