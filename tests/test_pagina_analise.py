import os
from dataclasses import replace

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from ui.calculo import CurvaModelo, Falha, ResultadoAnalise, calcular
from ui.estado import EntradaComposito
from ui.paginas.analise import csv_pt_br, tabela_completa, tabela_em_fi

APP = os.path.join(os.path.dirname(__file__), '..', 'src', 'app.py')


@pytest.fixture(scope='module')
def resultado():
    return calcular(EntradaComposito())


def abrir_analise(resultado, entrada=None):
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state['hoop_resultado'] = resultado
    at.session_state['hoop_entrada'] = entrada or resultado.entrada
    at.session_state['hoop_etapa'] = 'analise'
    at.run()
    return at


def pagina_sem_resultado():
    from ui.paginas import analise
    analise.render()


def textos(elementos):
    return [e.value for e in elementos]


def com_falha_no_gsc(resultado):
    gsc = resultado.curvas['GSC']
    n = 87
    cortada = CurvaModelo('GSC', gsc.fis[:n], {k: v[:n] for k, v in gsc.valores.items()},
                          Falha(0.87, 'A equação não tem raiz real.'))
    return ResultadoAnalise(resultado.entrada, {**resultado.curvas, 'GSC': cortada})


def test_renderiza_metricas_e_grafico(resultado):
    at = abrir_analise(resultado)

    assert not at.exception
    assert at.title[0].value == 'Módulo de Young homogeneizado'
    metricas = {m.label: m.value for m in at.metric}
    assert metricas['Mori-Tanaka em fi 0,30'] == '38 235 MPa'
    assert metricas['Faixa Voigt–Reuss em fi 0,30'] == '36 207–42 339'
    assert 'Diferença entre MT, SC e GSC' in metricas
    assert len(at.get('image')) == 6
    assert not at.error and not at.warning and not at.info


def test_botoes_de_acao_navegam(resultado):
    at = abrir_analise(resultado)
    at.button(key='analise-relatorio').click()
    at.run()
    assert at.session_state['hoop_etapa'] == 'relatorio'


def test_estado_vazio_sem_resultado():
    at = AppTest.from_function(pagina_sem_resultado, default_timeout=30)
    at.run()

    assert not at.exception
    assert any('Ainda não há curvas para mostrar' in m.value for m in at.markdown)
    assert at.button(key='vazio-ir-dados').label == 'Ir para Dados'


def test_troca_de_grandeza(resultado):
    at = abrir_analise(resultado)
    at.segmented_control(key='analise-grandeza').set_value('vh')
    at.run()

    assert not at.exception
    assert at.title[0].value == 'Coeficiente de Poisson homogeneizado'
    assert at.metric[0].value.startswith('0,')


def test_leitura_em_outro_fi_e_entrada_invalida(resultado):
    at = abrir_analise(resultado)
    at.text_input(key='analise-fi').set_value('0.5')
    at.run()
    assert 'Mori-Tanaka em fi 0,50' in [m.label for m in at.metric]

    at.text_input(key='analise-fi').set_value('2')
    at.run()
    assert not at.exception
    assert 'Informe fi entre 0 e 1,00.' in textos(at.error)


def test_comparar_com_outro_modelo(resultado):
    at = abrir_analise(resultado)
    at.segmented_control(key='analise-comparar').set_value('GSC')
    at.run()

    assert 'GSC em fi 0,30' in [m.label for m in at.metric]
    assert 'vs GSC' in at.dataframe[0].value.columns


def test_csv_disponivel(resultado):
    at = abrir_analise(resultado)
    botao = at.get('download_button')[0]
    assert botao.proto.label == 'Baixar CSV'

    csv = csv_pt_br(tabela_completa(resultado, 'Eh')).decode('utf-8')
    linhas = csv.splitlines()
    assert linhas[0] == 'fi;Voigt;Reuss;Mori-Tanaka;Self-Consistent;GSC'
    assert len(linhas) == 102
    assert linhas[31].startswith('0,3;')


def test_falha_parcial_mostra_erro_e_mantem_curvas(resultado):
    at = abrir_analise(com_falha_no_gsc(resultado))

    assert not at.exception
    erro = textos(at.error)[0]
    assert 'GSC não foi calculado a partir de fi = 0,87' in erro
    assert 'Os outros 4 modelos' in erro
    assert at.metric[0].value == '38 235 MPa'


def test_dilute_fora_da_validade(resultado):
    entrada = replace(resultado.entrada, modelos=('Voigt', 'Reuss', 'Dilute Suspension'))
    at = abrir_analise(calcular(entrada))

    assert not at.exception
    assert 'Dilute Suspension vale até fi ≈ 0,10' in textos(at.warning)[0]
    tabela = at.dataframe[0].value
    assert tabela.set_index('Modelo').loc['Dilute Suspension'].iloc[1] == 'fora da validade'


def test_dados_alterados_e_recalcular(resultado):
    nova = replace(resultado.entrada, modelos=('Voigt', 'Reuss', 'Mori-Tanaka'))
    at = abrir_analise(resultado, entrada=nova)
    assert 'Os dados mudaram desde o último cálculo.' in textos(at.info)

    at.button(key='recalcular').click()
    at.run()
    assert not at.exception
    assert at.session_state['hoop_resultado'].entrada == nova
    assert not at.info


def test_tabela_em_fi_ordena_e_compara(resultado):
    tabela = tabela_em_fi(resultado, 'Eh', 0.30, 'Mori-Tanaka')
    assert list(tabela['Modelo']) == ['Voigt', 'Self-Consistent', 'GSC', 'Mori-Tanaka', 'Reuss']
    assert list(tabela['vs MT']) == ['+10,7%', '+0,9%', '+0,1%', 'ref.', '−5,3%']


def test_tabela_completa_preenche_falha_com_nan(resultado):
    tabela = tabela_completa(com_falha_no_gsc(resultado), 'Eh')
    assert len(tabela) == 101
    assert np.isnan(tabela['GSC'].iloc[-1]) and not np.isnan(tabela['GSC'].iloc[86])
