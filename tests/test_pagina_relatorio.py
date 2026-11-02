import os
from dataclasses import replace

import pytest
from streamlit.testing.v1 import AppTest

from hoop.ui.calculo import calcular
from hoop.ui.entrada import EntradaComposito
from hoop.ui.relatorio_analise import (OpcoesRelatorio, contar_paginas, gerar_pdf,
                                       linhas_tabela, nome_arquivo, titulo_padrao)

APP = os.path.join(os.path.dirname(__file__), '..', 'src', 'app.py')


@pytest.fixture(scope='module')
def resultado():
    return calcular(EntradaComposito())


def paginas_do_pdf(conteudo: bytes) -> int:
    return conteudo.count(b'/Type /Page\n')


# ── Domínio: gerar_pdf ─────────────────────────────────────────────────────

@pytest.mark.parametrize('secoes, esperado', [
    (dict(grafico_combinado=False, tabela=False), 1),
    (dict(), 3),
    (dict(graficos_por_modelo=True), 8),
    (dict(grafico_combinado=False, graficos_por_modelo=True), 7),
])
def test_pdf_tem_as_paginas_das_secoes(resultado, secoes, esperado):
    opcoes = OpcoesRelatorio(titulo='Concreto', **secoes)
    conteudo = gerar_pdf(resultado, opcoes)
    assert conteudo.startswith(b'%PDF')
    assert paginas_do_pdf(conteudo) == esperado == contar_paginas(resultado, opcoes)


def test_pdf_aceita_acentos_nu_e_autor(resultado):
    opcoes = OpcoesRelatorio(titulo='Concreto com inclusões esféricas — teste',
                             autor='Cllpsy', grandeza='vh')
    assert gerar_pdf(resultado, opcoes).startswith(b'%PDF')


def test_pdf_sem_modelos_calculados_gera_erro(resultado):
    vazio = replace(resultado, curvas={})
    with pytest.raises(ValueError, match='Nenhum modelo'):
        gerar_pdf(vazio, OpcoesRelatorio(titulo='x'))


def test_pdf_sem_deprecation_warning(resultado, recwarn):
    gerar_pdf(resultado, OpcoesRelatorio(titulo='x'))
    assert not [w for w in recwarn if issubclass(w.category, DeprecationWarning)]


def test_tabela_usa_fi_050_e_fi_max(resultado):
    linhas = dict((m, (a, b)) for m, a, b in linhas_tabela(resultado, 'Eh'))
    assert linhas['Voigt'] == ('50 318', '70 000')
    assert linhas['MT'] == ('45 071', '70 000')


def test_titulo_e_nome_do_arquivo_vem_do_preset_e_da_geometria():
    entrada = EntradaComposito()
    assert titulo_padrao(entrada) == 'Concreto com inclusões esféricas'
    assert nome_arquivo(entrada) == 'hoop-concreto-esfera.pdf'
    assert nome_arquivo(replace(entrada, material='epoxy_vidro')) == 'hoop-epoxy-vidro-esfera.pdf'


# ── Página Relatório ───────────────────────────────────────────────────────

def abrir_relatorio(resultado=None):
    at = AppTest.from_file(APP, default_timeout=60)
    if resultado is not None:
        at.session_state['hoop_resultado'] = resultado
        at.session_state['hoop_entrada'] = resultado.entrada
    at.session_state['hoop_etapa'] = 'relatorio'
    at.run()
    return at


def test_relatorio_mostra_o_botao_de_download(resultado):
    at = abrir_relatorio(resultado)
    assert not at.exception
    assert at.title[0].value == 'Relatório em PDF'
    botao = at.get('download_button')[0]
    assert botao.proto.label == 'Baixar PDF'
    assert botao.proto.type == 'primary'
    assert any('hoop-concreto-esfera.pdf' in m.value for m in at.markdown)
    assert any('3 páginas · A4' in m.value for m in at.markdown)


def test_relatorio_conta_paginas_extras_dos_graficos_por_modelo(resultado):
    at = abrir_relatorio(resultado)
    at.checkbox(key='relatorio-por-modelo').check().run()
    assert not at.exception
    assert any('8 páginas · A4' in m.value for m in at.markdown)


def test_relatorio_sem_resultado_cai_para_dados():
    at = abrir_relatorio()
    assert not at.exception
    assert at.session_state['hoop_etapa'] == 'relatorio'
    assert at.title[0].value == 'Defina o compósito'


def _pagina_sem_resultado():
    from hoop.ui.paginas import relatorio
    relatorio.render()


def test_pagina_sem_resultado_mostra_estado_vazio():
    at = AppTest.from_function(_pagina_sem_resultado, default_timeout=30).run()
    assert not at.exception
    assert not at.get('download_button')
    assert at.button(key='vazio-ir-dados').label == 'Ir para Dados'
