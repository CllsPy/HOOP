import os

import matplotlib.pyplot as plt
import numpy as np
import pytest

from cases._setup import criar_analise, MATERIAIS
from desenho.desenho_mec import DesenhoMecanico
from mecanico.geometrias import GeometriaCilindro
from mecanico.mecanico import Mecanico
from micmodelos.gsc import GSC
from micmodelos.moritanaka import MoriTanaka

APP = os.path.join(os.path.dirname(__file__), '..', 'src', 'app.py')


@pytest.fixture(autouse=True)
def sem_janelas(monkeypatch):
    monkeypatch.setattr(plt, 'show', lambda *a, **k: None)
    yield
    plt.close('all')


def test_mecanico_definir_tipo_nao_e_sombreado():
    m = Mecanico()
    assert m.tipo is None
    m.definir_tipo()
    assert m.matTipo == 'isotropico'


def test_cilindro_razao_de_aspecto_configuravel():
    padrao = GeometriaCilindro()
    assert padrao.razao_aspecto == pytest.approx(0.03 / 100)

    L = Mecanico().montaL(1000, 0.3)
    S_padrao = padrao.calcular_S(1000, 0.3, None, L)
    S_outro = GeometriaCilindro(razao_aspecto=0.1).calcular_S(1000, 0.3, None, L)
    assert not np.allclose(S_padrao, S_outro)


@pytest.mark.parametrize('estilo', ['fixar_fracao', 'normalizar', 'poisson'])
def test_curva_vai_de_zero_ate_fi_um(estilo):
    h = criar_analise(**MATERIAIS['concreto'])
    d = DesenhoMecanico(estilo=estilo)
    d.desenha(h, modelo=MoriTanaka())

    xs, ys, label = d.graphs[0]
    assert xs[0] == 0.0 and xs[-1] == 1.0
    assert len(xs) == 101
    assert label == 'Mori-Tanaka'


def test_juntar_grafs_sobrepoe_todos_os_modelos():
    h = criar_analise(**MATERIAIS['concreto'])
    d = DesenhoMecanico(estilo='normalizar')
    d.desenha(h, modelo=GSC())
    d.desenha(h, modelo=MoriTanaka())
    d.juntar_grafs(h)
    assert len(plt.gca().get_lines()) == 2


def test_app_streamlit_desenha_graficos_apos_envio():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception
    assert len(at.get('image')) == 0  # nada é calculado antes do envio

    at.multiselect[0].set_value(['GSC', 'MoriTanaka', 'SelfConsistent'])
    at.button[0].click()
    at.run()

    assert not at.exception
    assert not at.error
    assert len(at.expander) == 3
    assert len(at.get('image')) == 4  # 3 modelos + comparação


def test_app_streamlit_avisa_condutividade_indisponivel():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    at.selectbox[1].set_value('condutividade')
    at.button[0].click()
    at.run()

    assert not at.exception
    assert 'condutividade' in at.warning[0].value
