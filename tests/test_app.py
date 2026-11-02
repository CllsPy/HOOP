import os

import pytest
from streamlit.testing.v1 import AppTest

from hoop.ui.calculo import calcular
from hoop.ui.entrada import EntradaComposito

APP = os.path.join(os.path.dirname(__file__), '..', 'src', 'app.py')


@pytest.fixture
def app():
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    return at


def rotulos_das_etapas(at):
    return {b.label: b for b in at.sidebar.button}


def test_app_carrega_sem_excecao(app):
    assert not app.exception
    assert app.title[0].value == 'Defina o compósito'


def test_barra_lateral_mostra_as_tres_etapas(app):
    assert list(rotulos_das_etapas(app)) == ['Dados', 'Análise', 'Relatório']


def test_analise_e_relatorio_bloqueados_antes_de_calcular(app):
    etapas = rotulos_das_etapas(app)
    assert not etapas['Dados'].disabled
    assert etapas['Análise'].disabled and etapas['Relatório'].disabled
    assert 'Disponível depois de calcular' in [c.value for c in app.sidebar.caption]


def test_etapa_bloqueada_cai_para_dados(app):
    app.session_state['hoop_etapa'] = 'analise'
    app.run()
    assert app.title[0].value == 'Defina o compósito'


def test_depois_de_calcular_navega_para_analise(app):
    app.session_state['hoop_resultado'] = calcular(EntradaComposito(modelos=('Mori-Tanaka',)))
    app.run()
    rotulos_das_etapas(app)['Análise'].click()
    app.run()

    assert not app.exception
    assert app.title[0].value == 'Módulo de Young homogeneizado'
    assert not rotulos_das_etapas(app)['Relatório'].disabled
    assert 'Concreto · esfera · 1 modelo' in [c.value for c in app.sidebar.caption]
