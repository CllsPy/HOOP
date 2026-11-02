import os

import pytest
from streamlit.testing.v1 import AppTest

from ui.calculo import MODELOS_PADRAO, ResultadoAnalise
from ui.paginas.dados import texto_campo

APP = os.path.join(os.path.dirname(__file__), '..', 'src', 'app.py')


@pytest.fixture
def app():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    return at


def campo(at, nome):
    return at.text_input(key=f'dados-{nome}')


def botao_calcular(at):
    return at.button(key='dados-calcular')


def mensagens_de_erro(at):
    return [e.value for e in at.error]


def test_tela_abre_com_o_concreto(app):
    assert not app.exception
    assert app.title[0].value == 'Defina o compósito'
    assert campo(app, 'Em').value == '30 000'
    assert campo(app, 'vm').value == '0,20'
    assert app.pills(key='dados-preset').value == 'concreto'
    assert not botao_calcular(app).disabled


def test_preset_muda_os_valores(app):
    app.pills(key='dados-preset').set_value('aco_carbeto').run()

    assert campo(app, 'Em').value == '210 000'
    assert campo(app, 'Ei').value == '450 000'
    assert campo(app, 'vi').value == '0,24'
    assert app.session_state['hoop_entrada'].Em == 210_000


def test_editar_um_campo_leva_a_personalizado(app):
    campo(app, 'Em').input('31 000').run()

    assert app.pills(key='dados-preset').value == 'personalizado'
    assert app.session_state['hoop_entrada'].Em == 31_000
    assert any('Personalizado' in m.value for m in app.markdown)


def test_poisson_meio_mostra_erro_e_desabilita_calcular(app):
    campo(app, 'vm').input('0,5').run()

    assert any('menor que 0,5' in m for m in mensagens_de_erro(app))
    assert botao_calcular(app).disabled
    assert any('1 campo para corrigir' in m.value for m in app.markdown)


def test_texto_que_nao_e_numero_pede_correcao(app):
    campo(app, 'Ei').input('abc').run()

    assert any('Digite um número' in m for m in mensagens_de_erro(app))
    assert botao_calcular(app).disabled


def test_sem_modelos_desabilita_calcular(app):
    for nome in MODELOS_PADRAO:
        app.checkbox(key=f'dados-modelo-{nome}').uncheck()
    app.run()

    assert any('ao menos um modelo' in m for m in mensagens_de_erro(app))
    assert botao_calcular(app).disabled


def test_contraste_de_rigidez(app):
    assert any('Ei/Em = 2,33' in m.value for m in app.markdown)


def test_geometrias_futuras_desabilitadas(app):
    futuras = app.segmented_control(key='dados-geometria-futuras')
    assert futuras.disabled
    assert app.segmented_control(key='dados-geometria').value == 'esfera'
    assert app.segmented_control(key='dados-tipo').value == 'mecanica'


def test_restaurar_padrao_volta_ao_concreto(app):
    campo(app, 'vm').input('0,5').run()
    app.button(key='dados-restaurar').click().run()

    assert campo(app, 'vm').value == '0,20'
    assert not botao_calcular(app).disabled


def test_calcular_com_o_padrao_leva_a_analise(app):
    botao_calcular(app).click().run()

    assert not app.exception
    resultado = app.session_state['hoop_resultado']
    assert isinstance(resultado, ResultadoAnalise)
    assert resultado.calculados == MODELOS_PADRAO
    assert app.session_state['hoop_etapa'] == 'analise'
    assert app.title[0].value != 'Defina o compósito'


def test_voltar_para_dados_preserva_a_entrada(app):
    campo(app, 'Em').input('31 000').run()
    botao_calcular(app).click().run()
    app.sidebar.button(key='ir-dados').click().run()

    assert campo(app, 'Em').value == '31 000'


@pytest.mark.parametrize('valor, casas, esperado', [
    (30000, 0, '30 000'), (0.2, 2, '0,20'), (0.255, 2, '0,255'), (3500.5, 0, '3 500,5'),
])
def test_texto_campo(valor, casas, esperado):
    assert texto_campo(valor, casas) == esperado
