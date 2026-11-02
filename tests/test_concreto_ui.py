"""Modo "Concreto multiescala" da interface: núcleo da tela, páginas e PDF."""
import os
from dataclasses import replace

import pytest
from streamlit.testing.v1 import AppTest

from hoop.homogenizacao.multiescala import calcular_concreto
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.quatrofases import QuatroFases
from hoop.ui.concreto import (EntradaConcreto, PropriedadesFase, aviso_validade,
                              calcular_concreto_ui, eh_padrao_da_tese, escolher_destaque,
                              fases_concreto, previa_niveis, restaurar_tese,
                              resumo_analise_concreto, validar_concreto)
from hoop.ui.paginas.analise_concreto import tabela_por_nivel, tabela_propriedades
from hoop.ui.relatorio_multiescala import (OpcoesRelatorioConcreto, contar_paginas_concreto,
                                           gerar_pdf_concreto, linhas_fracoes,
                                           observacoes_concreto)
from hoop.ui.tema import CORES_FASE, SERIES

APP = os.path.join(os.path.dirname(__file__), '..', 'src', 'app.py')
SEM_ZTI_COM_REUSS = replace(EntradaConcreto(), construcao='sem_zti',
                            modelos_sem_zti=('Mori-Tanaka', 'Reuss'), modelo_poros='mesmo')


@pytest.fixture
def app():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    return at


@pytest.fixture(scope='module')
def resultado_tese():
    return calcular_concreto_ui(replace(EntradaConcreto(),
                                        modelos_zti=('Quatro fases', 'Múltiplas fases')))


def ir_para_concreto(at):
    at.segmented_control(key='dados-modo').set_value('concreto').run()
    assert not at.exception


def calcular(at):
    at.button(key='concreto-calcular').click().run()
    assert not at.exception


def metricas(at):
    return {m.label: m.value for m in at.metric}


# --- Núcleo da tela (sem Streamlit) ---------------------------------------------

def test_padrao_e_li_2019_em_mpa():
    entrada = EntradaConcreto()
    assert eh_padrao_da_tese(entrada)
    assert entrada.pasta == PropriedadesFase(21_340.0, 0.25, 0.154)
    assert entrada.E_experimental == 34_500.0 and entrada.poros == 0.0242
    assert not validar_concreto(entrada)


@pytest.mark.parametrize('construcao', ['com_zti', 'sem_zti'])
def test_previa_usa_as_mesmas_fracoes_do_nucleo(construcao):
    entrada = replace(EntradaConcreto(), construcao=construcao)
    modelo = QuatroFases() if construcao == 'com_zti' else MoriTanaka()
    nucleo = calcular_concreto(fases_concreto(entrada), modelo, entrada.com_zti)
    previa = previa_niveis(entrada)
    assert len(previa) == len(nucleo.niveis) == 3
    for nivel_previa, nivel_nucleo in zip(previa, nucleo.niveis):
        assert nivel_previa.nome == nivel_nucleo.nome
        assert [f.fracao for f in nivel_previa.fases] == pytest.approx(nivel_nucleo.fracoes)


def test_previa_com_zti_bate_com_a_tabela_7():
    linhas = linhas_fracoes(calcular_concreto_ui(EntradaConcreto()))
    assert [l[2] for l in linhas] == ['26,83%', '46,86%', '26,31%', '57,40%', '40,30%',
                                      '2,30%', '97,64%', '2,36%']


def test_sem_poros_ficam_dois_niveis():
    assert len(previa_niveis(replace(EntradaConcreto(), poros=0.0))) == 2


def test_soma_das_fracoes_diferente_de_100_e_erro():
    entrada = replace(EntradaConcreto(), pasta=PropriedadesFase(21_340.0, 0.25, 0.20))
    erros = validar_concreto(entrada)
    assert 'soma' in erros and '104,60%' in erros['soma'] and 'Ajuste para 100%' in erros['soma']


@pytest.mark.parametrize('campo, valor, chave', [
    ('poros', 1.0, 'poros'), ('E_experimental', -1.0, 'E_experimental'),
    ('modelos_zti', (), 'modelos'),
])
def test_validacao_de_campos(campo, valor, chave):
    assert chave in validar_concreto(replace(EntradaConcreto(), **{campo: valor}))


def test_poisson_meio_e_pasta_sem_fracao_sao_erros():
    entrada = replace(EntradaConcreto(), zti_miudo=PropriedadesFase(12_700.0, 0.5, 0.151),
                      pasta=PropriedadesFase(21_340.0, 0.25, 0.0))
    erros = validar_concreto(entrada)
    assert 'menor que 0,5' in erros['zti_miudo.v']
    assert 'maior que zero' in erros['pasta.fracao']


def test_restaurar_tese_mantem_construcao_e_modelos():
    editada = replace(EntradaConcreto(), construcao='sem_zti', poros=0.0,
                      modelos_sem_zti=('GSC',), E_experimental=None)
    restaurada = restaurar_tese(editada)
    assert eh_padrao_da_tese(restaurada)
    assert restaurada.construcao == 'sem_zti' and restaurada.modelos_sem_zti == ('GSC',)


def test_quatro_fases_reproduz_o_nucleo_em_mpa(resultado_tese):
    serie = resultado_tese.series['Quatro fases']
    assert serie.Eh == pytest.approx(34_645.1, abs=0.5)
    assert abs(serie.erro_relativo) < 0.01
    assert [n.resultado.Eh for n in serie.niveis] == pytest.approx([30_785, 36_321, 34_645],
                                                                   abs=1)
    assert resultado_tese.calculados == ('Quatro fases', 'Múltiplas fases')


def test_sem_zti_mori_tanaka_bate_com_a_tabela_6():
    entrada = replace(EntradaConcreto(), construcao='sem_zti', modelos_sem_zti=('Mori-Tanaka',))
    serie = calcular_concreto_ui(entrada).series['Mori-Tanaka']
    assert [n.resultado.Eh for n in serie.niveis] == pytest.approx([45_614, 48_341, 45_671],
                                                                   abs=1)


def test_modelo_que_falha_nos_poros_guarda_os_niveis_1_e_2():
    resultado = calcular_concreto_ui(SEM_ZTI_COM_REUSS)
    reuss = resultado.series['Reuss']
    assert reuss.falha.nivel == 3 and 'poros' in reuss.falha.mensagem
    assert len(reuss.niveis) == 2 and reuss.Eh is None
    assert resultado.calculados == ('Mori-Tanaka',)


def test_tabelas_da_analise(resultado_tese):
    por_nivel = tabela_por_nivel(resultado_tese)
    assert list(por_nivel.columns) == ['Modelo', 'Nível 1', 'Nível 2', 'Nível 3', 'Erro']
    assert por_nivel.iloc[0].tolist() == ['Quatro fases', '30 785', '36 321', '34 645', '+0,42%']
    propriedades = tabela_propriedades(resultado_tese)
    assert len(propriedades) == 6
    assert list(propriedades.columns)[3:] == ['E [MPa]', 'ν', 'K [MPa]', 'G [MPa]']


def test_novas_cores_sao_tokens_do_tema():
    assert SERIES['Quatro fases'] and SERIES['Múltiplas fases']
    assert SERIES['Quatro fases'] != SERIES['Múltiplas fases']
    for fase in ('pasta', 'agregado_miudo', 'agregado_graudo', 'zti_miudo', 'zti_graudo', 'poros'):
        assert CORES_FASE[fase].startswith('#')


# --- PDF ----------------------------------------------------------------------------

@pytest.mark.parametrize('grafico, tabela, paginas', [
    (True, True, 3), (False, True, 2), (False, False, 1),
])
def test_pdf_multiescala(resultado_tese, grafico, tabela, paginas):
    opcoes = OpcoesRelatorioConcreto('Concreto multiescala com ZTI', 'Autora ν',
                                     grafico=grafico, tabela=tabela)
    dados = gerar_pdf_concreto(resultado_tese, opcoes)
    assert dados.startswith(b'%PDF')
    assert contar_paginas_concreto(opcoes) == paginas
    assert dados.count(b'/Type /Page') - dados.count(b'/Type /Pages') == paginas


def test_pdf_com_modelo_que_falhou():
    dados = gerar_pdf_concreto(calcular_concreto_ui(SEM_ZTI_COM_REUSS),
                               OpcoesRelatorioConcreto('Concreto sem ZTI'))
    assert dados.startswith(b'%PDF')


# --- Tela -----------------------------------------------------------------------------

def test_duas_fases_continua_o_padrao(app):
    assert app.segmented_control(key='dados-modo').value == 'duas_fases'
    assert app.title[0].value == 'Defina o compósito'
    assert app.text_input(key='dados-Em').value == '30 000'


def test_alternar_para_concreto_e_voltar(app):
    ir_para_concreto(app)
    assert app.title[0].value == 'Defina o concreto'
    assert app.session_state['hoop_modo'] == 'concreto'
    assert app.text_input(key='concreto-pasta-E').value == '21 340'
    assert app.text_input(key='concreto-pasta-fracao').value == '15,4'
    assert app.text_input(key='concreto-poros').value == '2,42'
    assert app.text_input(key='concreto-E_exp').value == '34 500'
    assert not app.button(key='concreto-calcular').disabled
    assert [b.key for b in app.main.button if b.proto.type == 'primary'] == ['concreto-calcular']

    app.segmented_control(key='dados-modo').set_value('duas_fases').run()
    assert app.title[0].value == 'Defina o compósito'
    assert app.text_input(key='dados-Em').value == '30 000'
    assert app.pills(key='dados-preset').value == 'concreto'


def test_calcular_com_os_valores_da_tese(app):
    ir_para_concreto(app)
    calcular(app)
    assert app.title[0].value == 'Módulo de Young do concreto'
    valores = metricas(app)
    assert valores['E do concreto · Quatro fases'] == '34 645 MPa'
    assert valores['Erro vs experimental'] == '+0,42%'
    erro = app.session_state['hoop_resultado_concreto'].series['Quatro fases'].erro_relativo
    assert abs(erro) < 0.01
    assert not app.error
    assert 'Concreto · com ZTI · 1 modelo' in [c.value for c in app.sidebar.caption]


def test_fracoes_que_nao_somam_100_bloqueiam_o_calculo(app):
    ir_para_concreto(app)
    app.text_input(key='concreto-pasta-fracao').input('20').run()
    assert any('somam 104,60%' in e.value for e in app.error)
    assert app.button(key='concreto-calcular').disabled
    assert any('1 campo para corrigir' in m.value for m in app.markdown)


def test_texto_invalido_mostra_erro_junto_do_campo(app):
    ir_para_concreto(app)
    app.text_input(key='concreto-zti_graudo-E').input('abc').run()
    assert any('Digite um número' in e.value for e in app.error)
    assert app.button(key='concreto-calcular').disabled


def test_restaurar_valores_da_tese(app):
    ir_para_concreto(app)
    app.text_input(key='concreto-pasta-E').input('25 000').run()
    app.text_input(key='concreto-E_exp').input('').run()
    assert app.session_state['hoop_entrada_concreto'].pasta.E == 25_000
    assert app.session_state['hoop_entrada_concreto'].E_experimental is None

    app.button(key='concreto-restaurar').click().run()
    assert app.text_input(key='concreto-pasta-E').value == '21 340'
    assert app.text_input(key='concreto-E_exp').value == '34 500'
    assert eh_padrao_da_tese(app.session_state['hoop_entrada_concreto'])


def test_trocar_para_sem_zti_e_calcular(app):
    ir_para_concreto(app)
    app.segmented_control(key='concreto-construcao').set_value('sem_zti').run()
    assert app.checkbox(key='concreto-modelo-Mori-Tanaka').value
    assert app.checkbox(key='concreto-modelo-GSC').value
    calcular(app)
    resultado = app.session_state['hoop_resultado_concreto']
    assert resultado.calculados == ('Mori-Tanaka', 'Self-Consistent', 'GSC')
    assert resultado.series['Mori-Tanaka'].Eh == pytest.approx(45_671, abs=1)
    assert app.segmented_control(key='concreto-analise-destaque').value == 'Mori-Tanaka'

    app.sidebar.button(key='ir-dados').click().run()
    app.segmented_control(key='concreto-construcao').set_value('com_zti').run()
    assert app.checkbox(key='concreto-modelo-Quatro fases').value
    assert app.session_state['hoop_entrada_concreto'].modelos_sem_zti == (
        'Mori-Tanaka', 'Self-Consistent', 'GSC')


def test_modelo_que_falha_aparece_como_aviso_sem_derrubar_os_outros(app):
    ir_para_concreto(app)
    app.segmented_control(key='concreto-construcao').set_value('sem_zti').run()
    app.checkbox(key='concreto-modelo-Reuss').check().run()
    app.segmented_control(key='concreto-modelo-poros').set_value('mesmo').run()
    calcular(app)
    erros = [e.value for e in app.error]
    assert any('Reuss não foi calculado no nível 3' in e and 'calculados normalmente' in e
               for e in erros)
    assert 'E do concreto · Mori-Tanaka' in metricas(app)


def test_relatorio_multiescala_gera_o_pdf(app):
    ir_para_concreto(app)
    calcular(app)
    app.button(key='analise-relatorio').click().run()
    assert not app.exception
    assert app.title[0].value == 'Relatório em PDF'
    botao = app.get('download_button')[0].proto
    assert botao.label == 'Baixar PDF' and botao.type == 'primary'
    assert not [b for b in app.main.button if b.proto.type == 'primary']
    assert app.text_input(key='relatorio-titulo').value == 'Concreto multiescala com ZTI'
    assert 'Quatro fases · Ec 34 645 MPa' in [c.value for c in app.sidebar.caption]


def test_cada_modo_guarda_o_seu_resultado(app):
    app.button(key='dados-calcular').click().run()
    assert metricas(app)['Mori-Tanaka em fi 0,30'] == '38 235 MPa'
    app.sidebar.button(key='ir-dados').click().run()

    ir_para_concreto(app)
    assert app.sidebar.button(key='ir-analise').disabled  # concreto ainda não calculado
    calcular(app)
    app.sidebar.button(key='ir-dados').click().run()
    app.segmented_control(key='dados-modo').set_value('duas_fases').run()
    app.sidebar.button(key='ir-analise').click().run()
    assert app.title[0].value == 'Módulo de Young homogeneizado'
    assert metricas(app)['Mori-Tanaka em fi 0,30'] == '38 235 MPa'


# --- Revisão: domínio dos modelos, destaque e estado dos widgets ----------------

SO_DILUTE = replace(EntradaConcreto(), construcao='sem_zti',
                    modelos_sem_zti=('Dilute Suspension',), modelo_poros='mesmo')


def entrada_na_sessao(at):
    return at.session_state['hoop_entrada_concreto']


def test_E_negativo_vira_falha_e_nao_resultado():
    resultado = calcular_concreto_ui(replace(SO_DILUTE, poros=0.95))
    serie = resultado.series['Dilute Suspension']
    assert not serie.completa and serie.falha.nivel == 3
    assert 'E nulo ou negativo' in serie.falha.mensagem
    assert all(n.resultado.Eh > 0 for n in serie.niveis)


def test_dilute_acima_da_validade_fica_registrado_e_vai_ao_pdf():
    resultado = calcular_concreto_ui(SO_DILUTE)
    serie = resultado.series['Dilute Suspension']
    assert serie.completa and serie.fora_da_validade == (1, 2)
    aviso = aviso_validade(resultado, 'Dilute Suspension')
    assert 'vale até fi ≈ 0,10' in aviso and '63,6%' in aviso
    assert aviso in observacoes_concreto(resultado)
    assert calcular_concreto_ui(SEM_ZTI_COM_REUSS).series['Mori-Tanaka'].fora_da_validade == ()


def test_zti_sem_o_seu_agregado_e_erro_no_campo_do_agregado():
    entrada = replace(EntradaConcreto(), pasta=PropriedadesFase(21_340.0, 0.25, 0.423),
                      agregado_miudo=PropriedadesFase(77_600.0, 0.15, 0.0))
    erros = validar_concreto(entrada)
    assert set(erros) == {'agregado_miudo.fracao'}
    assert 'zere a ZTI' in erros['agregado_miudo.fracao']
    assert not validar_concreto(replace(entrada, construcao='sem_zti'))


def test_destaque_padrao_evita_os_limites():
    entrada = replace(EntradaConcreto(), construcao='sem_zti',
                      modelos_sem_zti=('Voigt', 'Reuss', 'Self-Consistent', 'Mori-Tanaka'))
    resultado = calcular_concreto_ui(entrada)
    assert escolher_destaque(resultado) == 'Mori-Tanaka'
    assert escolher_destaque(resultado, 'Voigt') == 'Voigt'
    assert escolher_destaque(resultado, 'Quatro fases') == 'Mori-Tanaka'
    assert resumo_analise_concreto(resultado).startswith('Mori-Tanaka · Ec')


def test_pdf_destaca_o_modelo_escolhido(resultado_tese, monkeypatch):
    import hoop.ui.relatorio_multiescala as rel
    destacados = []
    monkeypatch.setattr(rel, 'imagem_niveis',
                        lambda r, d=None, dpi=0: destacados.append(d) or rel.imagem_png(
                            rel.figura_niveis(r, d), 50))
    gerar_pdf_concreto(resultado_tese, OpcoesRelatorioConcreto('T', destaque='Múltiplas fases'))
    gerar_pdf_concreto(resultado_tese, OpcoesRelatorioConcreto('T'))
    assert destacados == ['Múltiplas fases', 'Quatro fases']


def test_desmarcar_modelo_sobrevive_a_troca_de_construcao(app):
    ir_para_concreto(app)
    app.segmented_control(key='concreto-construcao').set_value('sem_zti').run()
    app.checkbox(key='concreto-modelo-GSC').uncheck().run()
    app.segmented_control(key='concreto-construcao').set_value('com_zti').run()
    app.segmented_control(key='concreto-construcao').set_value('sem_zti').run()
    assert not app.checkbox(key='concreto-modelo-GSC').value
    assert entrada_na_sessao(app).modelos_sem_zti == ('Mori-Tanaka', 'Self-Consistent')


def test_desmarcar_modelo_sobrevive_a_ida_e_volta_da_analise(app):
    ir_para_concreto(app)
    app.segmented_control(key='concreto-construcao').set_value('sem_zti').run()
    app.checkbox(key='concreto-modelo-GSC').uncheck().run()
    calcular(app)
    app.sidebar.button(key='ir-dados').click().run()
    assert not app.checkbox(key='concreto-modelo-GSC').value
    app.text_input(key='concreto-pasta-E').input('21 341').run()
    assert entrada_na_sessao(app).modelos_sem_zti == ('Mori-Tanaka', 'Self-Consistent')


def test_modelo_dos_poros_sobrevive_a_poros_zero(app):
    ir_para_concreto(app)
    app.segmented_control(key='concreto-construcao').set_value('sem_zti').run()
    app.segmented_control(key='concreto-modelo-poros').set_value('mesmo').run()
    app.text_input(key='concreto-poros').input('0').run()
    app.text_input(key='concreto-poros').input('2,42').run()
    assert app.segmented_control(key='concreto-modelo-poros').value == 'mesmo'
    assert entrada_na_sessao(app).modelo_poros == 'mesmo'


def test_escolhas_e_textos_sobrevivem_a_troca_de_modo(app):
    ir_para_concreto(app)
    app.segmented_control(key='concreto-construcao').set_value('sem_zti').run()
    app.checkbox(key='concreto-modelo-GSC').uncheck().run()
    app.text_input(key='concreto-pasta-E').input('25 000').run()
    app.segmented_control(key='dados-modo').set_value('duas_fases').run()
    ir_para_concreto(app)
    assert not app.checkbox(key='concreto-modelo-GSC').value
    assert app.text_input(key='concreto-pasta-E').value == '25 000'
    assert entrada_na_sessao(app).modelos_sem_zti == ('Mori-Tanaka', 'Self-Consistent')


def test_destaque_persiste_entre_etapas_e_vai_ao_relatorio(app):
    ir_para_concreto(app)
    app.checkbox(key='concreto-modelo-Múltiplas fases').check().run()
    calcular(app)
    app.segmented_control(key='concreto-analise-destaque').set_value('Múltiplas fases').run()
    app.button(key='analise-relatorio').click().run()
    assert any(c.value.startswith('Múltiplas fases · Ec') for c in app.sidebar.caption)
    app.sidebar.button(key='ir-analise').click().run()
    assert app.segmented_control(key='concreto-analise-destaque').value == 'Múltiplas fases'
    assert any(m.startswith('E do concreto · Múltiplas fases') for m in metricas(app))


def test_destaque_padrao_na_tela_nao_e_um_limite(app):
    ir_para_concreto(app)
    app.segmented_control(key='concreto-construcao').set_value('sem_zti').run()
    app.checkbox(key='concreto-modelo-Voigt').check().run()
    calcular(app)
    assert 'E do concreto · Mori-Tanaka' in metricas(app)


def test_dilute_com_poros_demais_aparece_como_falha(app):
    ir_para_concreto(app)
    app.segmented_control(key='concreto-construcao').set_value('sem_zti').run()
    for nome in ('Mori-Tanaka', 'Self-Consistent', 'GSC'):
        app.checkbox(key=f'concreto-modelo-{nome}').uncheck().run()
    app.checkbox(key='concreto-modelo-Dilute Suspension').check().run()
    app.segmented_control(key='concreto-modelo-poros').set_value('mesmo').run()
    app.text_input(key='concreto-poros').input('99').run()
    calcular(app)
    assert any('Dilute Suspension não foi calculado no nível 3' in e.value for e in app.error)
    assert any('vale até fi ≈ 0,10' in w.value for w in app.warning)
    assert not any('−' in v for v in metricas(app).values())


def test_zti_sem_agregado_bloqueia_o_calculo_junto_do_campo(app):
    ir_para_concreto(app)
    app.text_input(key='concreto-agregado_miudo-fracao').input('0').run()
    app.text_input(key='concreto-pasta-fracao').input('42,3').run()
    assert any('A ZTI do miúdo envolve o agregado miúdo' in e.value for e in app.error)
    assert app.button(key='concreto-calcular').disabled


def test_fracao_aceita_porcentagem_e_erros_falam_do_campo(app):
    ir_para_concreto(app)
    app.text_input(key='concreto-pasta-fracao').input('15,4%').run()
    assert not app.error and not app.button(key='concreto-calcular').disabled
    assert entrada_na_sessao(app).pasta.fracao == pytest.approx(0.154)
    app.text_input(key='concreto-pasta-fracao').input('abc').run()
    assert [e.value for e in app.error] == ['Digite a fração em %, como 15,4.']
    app.text_input(key='concreto-pasta-fracao').input('15,4').run()
    app.text_input(key='concreto-pasta-v').input('x').run()
    assert [e.value for e in app.error] == ['Digite um número, como 0,25.']


def test_mapa_de_etapas_descreve_o_concreto(app):
    ir_para_concreto(app)
    legendas = [c.value for c in app.sidebar.caption]
    assert 'Fases, ZTIs e poros' in legendas
    assert 'Curvas e comparação' not in legendas and 'Fases, geometria e modelos' not in legendas
    calcular(app)
    assert 'E por nível e erro' in [c.value for c in app.sidebar.caption]
    app.sidebar.button(key='ir-dados').click().run()
    app.segmented_control(key='dados-modo').set_value('duas_fases').run()
    assert 'Fases, geometria e modelos' in [c.value for c in app.sidebar.caption]
