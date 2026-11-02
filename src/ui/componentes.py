"""Peças de interface reutilizadas pelas telas (Streamlit + CSS de ``ui.tema``).

Funções que desenham: ``mapa_de_etapas``, ``cabecalho``, ``titulo_secao``,
``titulo_fase``, ``estado_vazio``, ``aviso_dados_alterados``.
Funções que devolvem HTML para ``st.markdown(..., unsafe_allow_html=True)``:
``rotulo_fase``, ``amostra_serie``, ``glifo``.
"""
from dataclasses import dataclass
from html import escape
from typing import Dict, Iterable, Optional

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from ui import estado as sessao
from ui.calculo import calcular
from ui.estado import ETAPAS, ir_para
from ui.tema import GLIFOS, SERIES, TRACEJADOS

VERSAO = 'HOOP v1.0 · baseado em Silva (2022)'


@dataclass(frozen=True)
class Etapa:
    nome: str
    icone: str
    descricao: str


ETAPAS_INFO: Dict[str, Etapa] = {
    'dados': Etapa('Dados', ':material/tune:', 'Fases, geometria e modelos'),
    'analise': Etapa('Análise', ':material/monitoring:', 'Curvas e comparação'),
    'relatorio': Etapa('Relatório', ':material/picture_as_pdf:', 'PDF com dados e resultados'),
}

ICONES_ESTADO = {
    'concluida': ':material/check_circle:',
    'atual': ':material/radio_button_checked:',
    'disponivel': ':material/radio_button_unchecked:',
    'bloqueada': ':material/radio_button_unchecked:',
}

FASES = {
    'matriz': ('Matriz', 'fase contínua', ':material/grid_on:'),
    'inclusao': ('Inclusão', 'partículas dispersas', ':material/bubble_chart:'),
}


def _estado_etapa(etapa: str, atual: str, liberadas: Iterable[str]) -> str:
    i, j = ETAPAS.index(etapa), ETAPAS.index(atual)
    if i == j:
        return 'atual'
    if etapa not in liberadas:
        return 'bloqueada'
    return 'concluida' if i < j else 'disponivel'


def _descricao_etapa(etapa: str, estado: str, resumos: Dict[str, str]) -> str:
    if estado == 'bloqueada':
        return 'Disponível depois de calcular'
    return resumos.get(etapa) or ETAPAS_INFO[etapa].descricao


def marca() -> None:
    """Marca HOOP com o nome do app."""
    st.html(f'<div class="hoop-marca">{GLIFOS["marca"]}'
            '<div><b>HOOP</b><small>Homogeneização de compósitos</small></div></div>')


def mapa_de_etapas(etapa_atual: str, liberadas: Iterable[str],
                   resumos: Optional[Dict[str, str]] = None) -> None:
    """Sequence Map na barra lateral: marca, as 3 etapas e a versão.

    ``liberadas`` vem de ``estado.etapas_liberadas()``; ``resumos`` troca a
    descrição de uma etapa (ex.: {'dados': 'Concreto · esfera · 5 modelos'}).
    Clicar numa etapa liberada chama ``estado.ir_para``.
    """
    liberadas, resumos = set(liberadas), resumos or {}
    with st.sidebar:
        marca()
        for etapa in ETAPAS:
            estado = _estado_etapa(etapa, etapa_atual, liberadas)
            with st.container(key=f'passo-{estado}-{etapa}'):
                st.button(ETAPAS_INFO[etapa].nome, key=f'ir-{etapa}',
                          icon=ICONES_ESTADO[estado], type='tertiary',
                          disabled=estado == 'bloqueada',
                          on_click=ir_para, args=(etapa,))
                st.caption(_descricao_etapa(etapa, estado, resumos))
        st.caption(VERSAO)


def cabecalho(etapa_n: int, titulo: str, subtitulo: Optional[str] = None) -> DeltaGenerator:
    """Sobretítulo "Etapa n de 3", título e subtítulo (aceita HTML de ``rotulo_fase``).

    Devolve a coluna da direita, para as ações da tela.
    """
    texto, acoes = st.columns([3, 1], vertical_alignment='bottom')
    with texto:
        st.html(f'<span class="hoop-sobretitulo">Etapa {etapa_n} de {len(ETAPAS)}</span>')
        st.title(titulo, anchor=False)
        if subtitulo:
            st.markdown(f'<span class="hoop-mudo">{subtitulo}</span>', unsafe_allow_html=True)
    return acoes


def titulo_secao(icone: str, texto: str, detalhe: Optional[str] = None) -> None:
    """Título de seção com ícone Material (ex.: ``'science'``) e detalhe em cinza."""
    extra = f' <span class="hoop-mudo" style="font-size:13px">{escape(detalhe)}</span>' if detalhe else ''
    st.markdown(f'#### :material/{icone}: {escape(texto)}{extra}', unsafe_allow_html=True)


def rotulo_fase(fase: str, texto: str) -> str:
    """HTML do texto na cor da fase ('matriz' ou 'inclusao')."""
    return f'<span class="hoop-fase hoop-fase-{fase}">{escape(texto)}</span>'


def titulo_fase(fase: str) -> None:
    """Cabeçalho do PhaseCard: quadrado na cor da fase, ícone, nome e papel da fase."""
    nome, papel, icone = FASES[fase]
    st.markdown(
        f'#### <span class="hoop-fase-{fase}"><span class="hoop-quadrado" '
        f'style="background:currentColor" aria-hidden="true"></span></span>{icone} {nome} '
        f'<span class="hoop-mudo" style="font-size:13px;font-weight:400">{papel}</span>',
        unsafe_allow_html=True,
    )


def amostra_serie(nome: str) -> str:
    """HTML de um traço curto na cor da série do modelo (tracejado para os limites)."""
    classe = 'hoop-amostra hoop-amostra-tracejada' if nome in TRACEJADOS else 'hoop-amostra'
    return f'<span class="{classe}" style="border-color:{SERIES[nome]}" aria-hidden="true"></span>'


def glifo(nome: str) -> str:
    """HTML do glifo SVG ('esfera', 'cilindro', 'disco' ou 'marca') em tamanho de texto."""
    return f'<span class="hoop-glifo" aria-hidden="true">{GLIFOS[nome]}</span>'


def estado_vazio(titulo: str, texto: str) -> None:
    """Tela sem resultados, com o botão secundário "Ir para Dados"."""
    with st.container(border=True):
        st.markdown(f'### :material/monitoring: {escape(titulo)}')
        st.markdown(f'<span class="hoop-mudo">{escape(texto)}</span>', unsafe_allow_html=True)
        st.button('Ir para Dados', icon=':material/tune:', key='vazio-ir-dados',
                  on_click=ir_para, args=('dados',))


def aviso_dados_alterados(chave: str = 'recalcular') -> None:
    """Se a entrada mudou desde o cálculo, avisa e oferece "Recalcular"."""
    if not sessao.dados_mudaram():
        return
    texto, acao = st.columns([4, 1], vertical_alignment='center')
    texto.info('Os dados mudaram desde o último cálculo.', icon=':material/info:')
    if acao.button('Recalcular', icon=':material/refresh:', key=chave):
        recalcular()


def recalcular() -> None:
    """Recalcula com a entrada atual e reexecuta a página; erros de entrada viram st.error."""
    entrada = sessao.entrada_atual()
    erros = sessao.validar(entrada)
    if erros:
        st.error('Corrija os dados antes de recalcular: ' + ' '.join(erros.values()),
                 icon=':material/error:')
        return
    with st.spinner('Calculando os modelos…'):
        sessao.registrar_resultado(calcular(entrada))
    st.rerun()
