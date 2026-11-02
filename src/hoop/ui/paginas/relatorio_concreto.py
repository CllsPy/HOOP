"""Etapa 3 no modo "Concreto multiescala": prévia e download do PDF.

Mesmo layout do relatório de duas fases: à esquerda a prévia das páginas, à
direita título, autor, seções e "Baixar PDF", a única ação primária da tela.
"""
import base64
from html import escape
from typing import List

import streamlit as st

from hoop.ui import estado
from hoop.ui.acoes import recalcular
from hoop.ui.componentes import aviso_dados_alterados, cabecalho, estado_vazio
from hoop.ui.concreto import ResultadoConcreto, escolher_destaque
from hoop.ui.paginas.relatorio import (CHAVE_GERADO, _DPI_PREVIA, _SUBTITULO, _html_imagem,
                                       _html_legenda, _html_linha_dado, _html_linha_tabela,
                                       _html_pagina, _html_titulo, _paginas,
                                       _registrar_download)
from hoop.ui.relatorio_multiescala import (OpcoesRelatorioConcreto, contar_paginas_concreto,
                                           dados_concreto, gerar_pdf_concreto, imagem_niveis,
                                           linhas_fracoes, linhas_por_nivel,
                                           nome_arquivo_concreto, titulo_padrao_concreto)
from hoop.ui.tema import CORES


def render() -> None:
    resultado = estado.resultado_concreto_atual()
    cabecalho(3, 'Relatório em PDF', _SUBTITULO)
    if resultado is None:
        estado_vazio('Ainda não há resultados para o relatório',
                     'Defina as fases do concreto e os modelos. '
                     'O relatório fica disponível depois do cálculo.')
        return
    if aviso_dados_alterados('relatorio-recalcular'):
        recalcular()
    if not any(s.niveis for s in resultado.series.values()):
        st.error('Nenhum modelo chegou a calcular um nível. Volte a Dados e ajuste a entrada.',
                 icon=':material/error:')
        return
    previa, formulario = st.columns([3, 2], gap='large')
    with formulario:
        opcoes = _formulario(resultado)
    with previa:
        _previa(resultado, opcoes)


def _formulario(resultado: ResultadoConcreto) -> OpcoesRelatorioConcreto:
    padrao = titulo_padrao_concreto(resultado)
    with st.container(border=True):
        st.markdown('#### Conteúdo do relatório')
        titulo = st.text_input('Título', value=padrao, key='relatorio-titulo')
        autor = st.text_input('Autor (opcional)', key='relatorio-autor',
                              placeholder='Seu nome ou o do grupo')
        st.markdown('**Seções**')
        st.checkbox('Fases e frações por nível :gray[sempre incluída]', value=True,
                    disabled=True, key='relatorio-dados')
        grafico = st.checkbox('Gráfico por nível e erro', value=True,
                              key='relatorio-concreto-grafico')
        tabela = st.checkbox('Tabela de resultados (E, ν, K e G)', value=True,
                             key='relatorio-concreto-tabela')
        opcoes = OpcoesRelatorioConcreto(
            titulo=titulo.strip() or padrao, autor=autor, grafico=grafico, tabela=tabela,
            destaque=escolher_destaque(resultado, estado.destaque_concreto_atual()))
        _arquivo(resultado, opcoes)
    return opcoes


def _arquivo(resultado: ResultadoConcreto, opcoes: OpcoesRelatorioConcreto) -> None:
    arquivo = nome_arquivo_concreto(resultado)
    st.markdown('**Arquivo**')
    st.markdown(f'<span class="hoop-dado">{escape(arquivo)}</span>  \n'
                f'<span class="hoop-mudo">{_paginas(contar_paginas_concreto(opcoes))} · A4'
                '</span>', unsafe_allow_html=True)
    with st.spinner('Gerando o PDF…'):
        dados = _pdf(resultado, resultado.entrada, opcoes)
    st.download_button('Baixar PDF', data=dados, file_name=arquivo, mime='application/pdf',
                       type='primary', icon=':material/download:', width='stretch',
                       key='relatorio-baixar', on_click=_registrar_download, args=(arquivo,))
    gerado = st.session_state.pop(CHAVE_GERADO, None)
    if gerado:
        st.success(f'PDF gerado: `{gerado}`', icon=':material/check_circle:')


@st.cache_data(max_entries=16, show_spinner=False)
def _pdf(_resultado: ResultadoConcreto, entrada, opcoes: OpcoesRelatorioConcreto) -> bytes:
    """PDF em cache pela entrada (que determina o resultado) e pelas opções."""
    return gerar_pdf_concreto(_resultado, opcoes)


@st.cache_data(max_entries=16, show_spinner=False)
def _miniatura(_resultado: ResultadoConcreto, entrada, destaque) -> str:
    return base64.b64encode(imagem_niveis(_resultado, destaque, dpi=_DPI_PREVIA)).decode('ascii')


def _previa(resultado: ResultadoConcreto, opcoes: OpcoesRelatorioConcreto) -> None:
    """Miniaturas das páginas A4 em HTML, com o mesmo conteúdo do PDF."""
    total = contar_paginas_concreto(opcoes)
    paginas = [_html_capa(resultado, opcoes)]
    if opcoes.grafico:
        imagem = _miniatura(resultado, resultado.entrada, opcoes.destaque)
        paginas.append(_html_imagem('3. E por nível', imagem,
                                    'Uma linha por modelo. Tracejado: E experimental.'))
    if opcoes.tabela:
        numero = 3 + int(opcoes.grafico)
        paginas.append(_html_resultados(resultado, numero))
    corpos = [_html_pagina(corpo, n, total, opcoes, larga=n == 1)
              for n, corpo in enumerate(paginas, start=1)]
    st.html(f'<section aria-label="Prévia do PDF" style="background:{CORES["surface-2"]};'
            'border-radius:10px;padding:24px;display:flex;flex-wrap:wrap;gap:20px;'
            f'align-items:flex-start">{"".join(corpos)}</section>')


def _html_tabela(titulos: List[str], linhas: List[List[str]]) -> str:
    corpo = [_html_linha_tabela(titulos, 'th')] + [_html_linha_tabela(l, 'td') for l in linhas]
    return ('<table style="border-collapse:collapse;width:100%;font-size:inherit;'
            f'font-variant-numeric:tabular-nums">{"".join(corpo)}</table>')


def _html_capa(resultado: ResultadoConcreto, opcoes: OpcoesRelatorioConcreto) -> str:
    subtitulo = ' · '.join(filter(None, ('Relatório de homogeneização multiescala',
                                         opcoes.autor.strip())))
    dados = ''.join(_html_linha_dado(r, v, f) for r, v, f in dados_concreto(resultado))
    fracoes = _html_tabela(['Nível', 'Fase', 'Fração'],
                           [list(l) for l in linhas_fracoes(resultado)])
    return (f'<b style="font-size:1.6em;line-height:1.2">{escape(opcoes.titulo)}</b>'
            f'{_html_legenda(subtitulo)}{_html_titulo("1. Fases e dados de entrada")}'
            f'<table style="border-collapse:collapse;width:100%;font-size:inherit">{dados}</table>'
            f'{_html_titulo("2. Frações por nível")}{fracoes}')


def _html_resultados(resultado: ResultadoConcreto, numero: int) -> str:
    cabecalho_tabela, linhas = linhas_por_nivel(resultado)
    return (f'{_html_titulo(f"{numero}. Resultados por nível")}'
            f'{_html_tabela(list(cabecalho_tabela), [list(l) for l in linhas])}'
            f'{_html_legenda("E em MPa. Na página: E, ν, K e G de cada nível.")}')
