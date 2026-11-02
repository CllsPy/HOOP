import matplotlib.pyplot as plt
import numpy as np
import pytest

from hoop.exemplos import criar_analise, MATERIAIS
from hoop.desenho.desenho_mec import DesenhoMecanico
from hoop.mecanico.geometrias import GeometriaCilindro
from hoop.mecanico.mecanico import Mecanico
from hoop.micmodelos.gsc import GSC
from hoop.micmodelos.moritanaka import MoriTanaka


@pytest.fixture(autouse=True)
def fechar_figuras():
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
    fig = d.juntar_grafs()
    assert len(fig.axes[0].get_lines()) == 2

