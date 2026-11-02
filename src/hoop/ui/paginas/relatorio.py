"""Etapa 3: relatório em PDF.

À esquerda, a prévia das páginas (Preview); à direita, título, autor, seções e
o botão "Baixar PDF", a única ação primária da tela.
"""
import base64
from html import escape
from typing import List

import streamlit as st

from hoop.ui import estado
from hoop.ui.acoes import recalcular
from hoop.ui.calculo import GRANDEZAS, ResultadoAnalise
from hoop.ui.componentes import aviso_dados_alterados, cabecalho, estado_vazio
from hoop.ui.formatacao import formatar_decimal
from hoop.ui.relatorio_analise import (OpcoesRelatorio, contar_paginas, dados_de_entrada,
                                       fi_intermediario, gerar_pdf, imagem_comparacao,
                                       imagem_modelo, legenda_valores, linhas_tabela,
                                       nome_arquivo, titulo_padrao)
from hoop.ui.tema import CORES, CORES_FASE

CHAVE_GERADO = 'relatorio-gerado'
_DPI_PREVIA = 72
_SUBTITULO = ('Confira as páginas e baixe o arquivo. O relatório usa os dados e os '
              'modelos da análise atual.')


def render() -> None:
    resultado = estado.resultado_atual()
    cabecalho(3, 'Relatório em PDF', _SUBTITULO)
    if resultado is None:
        estado_vazio('Ainda não há resultados para o relatório',
                     'Defina a matriz, a inclusão e os modelos. '
                     'O relatório fica disponível depois do cálculo.')
        return
    if aviso_dados_alterados('relatorio-recalcular'):
        recalcular()
    if not resultado.calculados:
        st.error('Nenhum modelo chegou a calcular um ponto. Volte a Dados e ajuste a entrada.',
                 icon=':material/error:')
        return
    previa, formulario = st.columns([3, 2], gap='large')
    with formulario:
        opcoes = _formulario(resultado)
    with previa:
        _previa(resultado, opcoes)


def _formulario(resultado: ResultadoAnalise) -> OpcoesRelatorio:
    entrada = resultado.entrada
    with st.container(border=True):
        st.markdown('#### Conteúdo do relatório')
        titulo = st.text_input('Título', value=titulo_padrao(entrada), key='relatorio-titulo')
        autor = st.text_input('Autor (opcional)', key='relatorio-autor',
                              placeholder='Seu nome ou o do grupo')
        opcoes = OpcoesRelatorio(titulo=titulo.strip() or titulo_padrao(entrada),
                                 autor=autor, grandeza=estado.leitura_atual().grandeza, **_secoes(resultado))
        _arquivo(resultado, opcoes)
    return opcoes


def _secoes(resultado: ResultadoAnalise) -> dict:
    st.markdown('**Seções**')
    st.checkbox('Dados de entrada :gray[sempre incluída]', value=True, disabled=True,
                key='relatorio-dados')
    combinado = st.checkbox('Gráfico combinado', value=True, key='relatorio-combinado')
    fi = formatar_decimal(fi_intermediario(resultado.entrada.fi_max))
    tabela = st.checkbox(f'Tabela por modelo (fi {fi} e fi máx.)', value=True,
                         key='relatorio-tabela')
    extras = len(resultado.calculados)
    por_modelo = st.checkbox(f'Um gráfico por modelo :gray[+{_paginas(extras)}]', value=False,
                             key='relatorio-por-modelo')
    return dict(grafico_combinado=combinado, tabela=tabela, graficos_por_modelo=por_modelo)


def _paginas(n: int) -> str:
    return f'{n} página' if n == 1 else f'{n} páginas'


def _arquivo(resultado: ResultadoAnalise, opcoes: OpcoesRelatorio) -> None:
    arquivo = nome_arquivo(resultado.entrada)
    st.markdown('**Arquivo**')
    st.markdown(f'<span class="hoop-dado">{escape(arquivo)}</span>  \n'
                f'<span class="hoop-mudo">{_paginas(contar_paginas(resultado, opcoes))} · A4'
                '</span>', unsafe_allow_html=True)
    with st.spinner('Gerando o PDF…'):
        dados = _pdf(resultado, resultado.entrada, opcoes)
    st.download_button('Baixar PDF', data=dados, file_name=arquivo, mime='application/pdf',
                       type='primary', icon=':material/download:', width='stretch',
                       key='relatorio-baixar', on_click=_registrar_download, args=(arquivo,))
    gerado = st.session_state.pop(CHAVE_GERADO, None)
    if gerado:
        st.success(f'PDF gerado: `{gerado}`', icon=':material/check_circle:')


def _registrar_download(arquivo: str) -> None:
    st.session_state[CHAVE_GERADO] = arquivo
    st.toast(f'PDF gerado: {arquivo}', icon=':material/check_circle:')


@st.cache_data(max_entries=16, show_spinner=False)
def _pdf(_resultado: ResultadoAnalise, entrada, opcoes: OpcoesRelatorio) -> bytes:
    """PDF em cache pela entrada (que determina o resultado) e pelas opções."""
    return gerar_pdf(_resultado, opcoes)


@st.cache_data(max_entries=64, show_spinner=False)
def _miniatura(_resultado: ResultadoAnalise, entrada, grandeza: str, modelo: str = '') -> str:
    """PNG em base64 do gráfico combinado ou, com ``modelo``, do gráfico desse modelo."""
    if modelo:
        png = imagem_modelo(_resultado, modelo, grandeza, dpi=_DPI_PREVIA)
    else:
        png = imagem_comparacao(_resultado, grandeza, dpi=_DPI_PREVIA)
    return base64.b64encode(png).decode('ascii')


def _previa(resultado: ResultadoAnalise, opcoes: OpcoesRelatorio) -> None:
    """Miniaturas das páginas A4 em HTML, com o mesmo conteúdo do PDF."""
    total = contar_paginas(resultado, opcoes)
    paginas = [_html_capa(resultado, opcoes)]
    if opcoes.grafico_combinado:
        paginas.append(_html_grafico(resultado, opcoes.grandeza, len(paginas) + 1))
    if opcoes.tabela:
        paginas.append(_html_tabela(resultado, opcoes.grandeza, len(paginas) + 1))
    if opcoes.graficos_por_modelo:
        secao = len(paginas) + 1
        for i, nome in enumerate(resultado.calculados, start=1):
            imagem = _miniatura(resultado, resultado.entrada, opcoes.grandeza, nome)
            paginas.append(_html_imagem(f'{secao}.{i} {nome}', imagem, ''))
    corpos = [_html_pagina(corpo, n, total, opcoes, larga=n == 1)
              for n, corpo in enumerate(paginas, start=1)]
    st.html(f'<section aria-label="Prévia do PDF" style="background:{CORES["surface-2"]};'
            'border-radius:10px;padding:24px;display:flex;flex-wrap:wrap;gap:20px;'
            f'align-items:flex-start">{"".join(corpos)}</section>')


def _html_pagina(corpo: str, n: int, total: int, opcoes: OpcoesRelatorio, larga: bool) -> str:
    largura, fonte = (300, 9) if larga else (200, 7)
    data = opcoes.data.strftime('%d/%m/%Y') + ' · ' if n == 1 else ''
    return (f'<article aria-label="Página {n}" style="flex:0 0 {largura}px;max-width:100%;'
            f'aspect-ratio:210/297;box-sizing:border-box;background:{CORES["surface-1"]};'
            'box-shadow:0 1px 3px rgba(20,33,32,.18);padding:16px 14px;display:flex;'
            f'flex-direction:column;gap:8px;font-size:{fonte}px;line-height:1.4;'
            f'color:{CORES["ink"]};overflow:hidden">'
            f'<div style="display:flex;justify-content:space-between;border-bottom:1px solid '
            f'{CORES["line"]};padding-bottom:4px"><b style="color:{CORES["accent"]}">HOOP</b>'
            f'<span style="color:{CORES["ink-muted"]}">{data}p. {n} de {total}</span></div>'
            f'{corpo}</article>')


def _html_titulo(texto: str) -> str:
    return f'<b style="font-size:1.15em">{escape(texto)}</b>'


def _html_legenda(texto: str) -> str:
    return f'<span style="color:{CORES["ink-muted"]}">{escape(texto)}</span>'


def _html_capa(resultado: ResultadoAnalise, opcoes: OpcoesRelatorio) -> str:
    subtitulo = ' · '.join(filter(None, ('Relatório de homogeneização', opcoes.autor.strip())))
    linhas = ''.join(_html_linha_dado(*linha) for linha in dados_de_entrada(resultado))
    return (f'<b style="font-size:1.6em;line-height:1.2">{escape(opcoes.titulo)}</b>'
            f'{_html_legenda(subtitulo)}{_html_titulo("1. Dados de entrada")}'
            f'<table style="border-collapse:collapse;width:100%;font-size:inherit">{linhas}</table>')


def _html_linha_dado(rotulo: str, valor: str, fase) -> str:
    cor = CORES_FASE[fase] if fase else CORES['ink-muted']
    peso = 600 if fase else 400
    borda = f'border-bottom:1px solid {CORES["line"]};padding:3px 0'
    return (f'<tr><td style="{borda};color:{cor};font-weight:{peso}">{escape(rotulo)}</td>'
            f'<td style="{borda}">{escape(valor)}</td></tr>')


def _html_grafico(resultado: ResultadoAnalise, grandeza: str, n: int) -> str:
    imagem = _miniatura(resultado, resultado.entrada, grandeza)
    legenda = f'{GRANDEZAS[grandeza].rotulo} em função de fi. Faixa cinza: Voigt–Reuss.'
    return _html_imagem(f'{n}. Gráfico combinado', imagem, legenda)


def _html_imagem(titulo: str, imagem_b64: str, legenda: str) -> str:
    return (f'{_html_titulo(titulo)}<img alt="" style="width:100%" '
            f'src="data:image/png;base64,{imagem_b64}">{_html_legenda(legenda)}')


def _html_tabela(resultado: ResultadoAnalise, grandeza: str, n: int) -> str:
    fi_max = resultado.entrada.fi_max
    titulos = ('Modelo', f'fi {formatar_decimal(fi_intermediario(fi_max))}',
                  f'fi {formatar_decimal(fi_max)}')
    linhas = [_html_linha_tabela(titulos, 'th')]
    linhas += [_html_linha_tabela(linha, 'td') for linha in linhas_tabela(resultado, grandeza)]
    return (f'{_html_titulo(f"{n}. Resultados por modelo")}'
            '<table style="border-collapse:collapse;width:100%;font-size:inherit;font-variant-numeric:'
            f'tabular-nums">{"".join(linhas)}</table>{_html_legenda(legenda_valores(grandeza))}')


def _html_linha_tabela(celulas: List[str], tag: str) -> str:
    borda = f'border-bottom:1px solid {CORES["line"]};padding:3px 0;white-space:nowrap'
    partes = [f'<{tag} style="{borda};text-align:{"left" if i == 0 else "right"};'
              f'font-weight:{600 if tag == "th" else 400}">{escape(c)}</{tag}>'
              for i, c in enumerate(celulas)]
    return f'<tr>{"".join(partes)}</tr>'
