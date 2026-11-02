"""Fluxo completo da interface: Dados → Análise → Relatório, pelo app inteiro."""
import os

import pytest
from streamlit.testing.v1 import AppTest

from hoop.ui.calculo import MODELOS_PADRAO
from hoop.ui.calculo import calcular as calcular_curvas
from hoop.ui.entrada import EntradaComposito
from hoop.ui.paginas.analise import (colorir_modelos, formatar_tabela_completa, tabela_completa,
                                     tabela_em_fi)
from hoop.ui.tema import SERIES

APP = os.path.join(os.path.dirname(__file__), '..', 'src', 'app.py')


@pytest.fixture
def app():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    return at


def calcular(at):
    at.button(key='dados-calcular').click().run()
    assert not at.exception


def legendas_da_barra(at):
    return [c.value for c in at.sidebar.caption]


def metricas(at):
    return {m.label: m.value for m in at.metric}


def baixar_pdf(at):
    return at.get('download_button')[0].proto


def test_fluxo_completo_com_o_concreto(app):
    assert app.title[0].value == 'Defina o compósito'
    assert app.pills(key='dados-preset').value == 'concreto'

    calcular(app)
    assert app.title[0].value == 'Módulo de Young homogeneizado'
    assert app.session_state['hoop_resultado'].calculados == MODELOS_PADRAO
    assert metricas(app)['Mori-Tanaka em fi 0,30'] == '38 235 MPa'

    app.segmented_control(key='analise-grandeza').set_value('Eh/Em').run()
    assert app.title[0].value == 'Módulo normalizado'
    app.segmented_control(key='analise-grandeza').set_value('vh').run()
    assert app.title[0].value == 'Coeficiente de Poisson homogeneizado'
    app.text_input(key='analise-fi').input('0,5').run()
    assert not app.exception and not app.error
    assert 'Mori-Tanaka em fi 0,50' in metricas(app)

    app.button(key='analise-relatorio').click().run()
    assert not app.exception
    assert app.title[0].value == 'Relatório em PDF'
    assert 'νh · leitura em fi 0,50' in legendas_da_barra(app)
    botao = baixar_pdf(app)
    assert botao.label == 'Baixar PDF' and botao.type == 'primary'


def test_relatorio_mantem_a_grandeza_depois_de_outra_interacao(app):
    calcular(app)
    app.segmented_control(key='analise-grandeza').set_value('vh').run()
    app.button(key='analise-relatorio').click().run()
    app.checkbox(key='relatorio-por-modelo').check().run()

    assert not app.exception
    assert app.session_state['hoop_leitura'].grandeza == 'vh'
    assert 'νh · leitura em fi 0,30' in legendas_da_barra(app)


def test_voltar_para_analise_preserva_a_leitura(app):
    calcular(app)
    app.segmented_control(key='analise-grandeza').set_value('Eh/Em').run()
    app.text_input(key='analise-fi').input('0,4').run()
    app.sidebar.button(key='ir-dados').click().run()
    app.sidebar.button(key='ir-analise').click().run()

    assert app.title[0].value == 'Módulo normalizado'
    assert app.text_input(key='analise-fi').value == '0,40'


def test_editar_dado_depois_de_calcular_avisa_na_analise(app):
    calcular(app)
    app.sidebar.button(key='ir-dados').click().run()
    app.text_input(key='dados-Em').input('31 000').run()
    app.sidebar.button(key='ir-analise').click().run()

    assert any('Os dados mudaram' in i.value for i in app.info)
    app.button(key='recalcular').click().run()
    assert not app.exception
    assert app.session_state['hoop_resultado'].entrada.Em == 31_000
    assert not app.info


def test_epoxi_com_fibra_de_carbono_calcula_sem_erro(app):
    app.pills(key='dados-preset').set_value('epoxy_carbono').run()
    calcular(app)

    resultado = app.session_state['hoop_resultado']
    assert resultado.entrada.material == 'epoxy_carbono'
    assert not resultado.falhas
    assert not app.error
    assert 'Epóxi + fibra de carbono · esfera · 5 modelos' in legendas_da_barra(app)


def test_poisson_meio_bloqueia_o_calculo(app):
    app.text_input(key='dados-vi').input('0,5').run()

    assert any('menor que 0,5' in e.value for e in app.error)
    assert app.button(key='dados-calcular').disabled
    assert app.sidebar.button(key='ir-analise').disabled


@pytest.mark.parametrize('etapa, primario', [
    ('dados', 'dados-calcular'), ('analise', 'analise-relatorio'),
])
def test_uma_acao_primaria_por_tela(app, etapa, primario):
    if etapa != 'dados':
        calcular(app)
    primarios = [b.key for b in app.main.button if b.proto.type == 'primary']
    assert primarios == [primario]


def test_relatorio_tem_so_o_download_como_acao_primaria(app):
    calcular(app)
    app.button(key='analise-relatorio').click().run()

    assert not [b for b in app.main.button if b.proto.type == 'primary']
    assert baixar_pdf(app).type == 'primary'


def test_tabela_da_analise_usa_as_cores_das_series():
    resultado = calcular_curvas(EntradaComposito())
    html = colorir_modelos(tabela_em_fi(resultado, 'Eh', 0.3, 'Mori-Tanaka')).to_html()
    for nome in resultado.calculados:
        assert SERIES[nome].lower() in html.lower()


def test_tabela_completa_usa_virgula_decimal():
    resultado = calcular_curvas(EntradaComposito(modelos=('Voigt',)))
    html = formatar_tabela_completa(tabela_completa(resultado, 'Eh'), 0).to_html()
    assert '0,30' in html and '42 339' in html
