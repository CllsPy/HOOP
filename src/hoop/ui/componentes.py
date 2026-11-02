"""Peças de interface reutilizadas pelas telas (Streamlit + CSS de ``hoop.ui.tema``).

Funções que desenham: ``mapa_de_etapas``, ``cabecalho``, ``seletor_modo``,
``titulo_secao``, ``titulo_fase``, ``estado_vazio``, ``aviso_dados_alterados``.
Funções que devolvem HTML para ``st.markdown(..., unsafe_allow_html=True)``:
``rotulo_fase``, ``amostra_serie``, ``glifo``.
"""
from dataclasses import dataclass
from html import escape
from typing import Dict, Iterable, Optional

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from hoop.ui import estado as sessao
from hoop.ui.concreto import FASES_CONCRETO
from hoop.ui.estado import ETAPAS, MODOS, ir_para
from hoop.ui.tema import GLIFOS, SERIES, TRACEJADOS

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

DESCRICOES_CONCRETO: Dict[str, str] = {
    'dados': 'Fases, ZTIs e poros',
    'analise': 'E por nível e erro',
}
"""Descrições das etapas no modo concreto (o que falta vem de ``ETAPAS_INFO``)."""

ICONES_ESTADO = {
    'concluida': ':material/check_circle:',
    'atual': ':material/radio_button_checked:',
    'disponivel': ':material/radio_button_unchecked:',
    'bloqueada': ':material/radio_button_unchecked:',
}

FASES = {
    'matriz': ('Matriz', 'fase contínua', ':material/grid_on:'),
    'inclusao': ('Inclusão', 'partículas dispersas', ':material/bubble_chart:'),
    **{f.chave: (f.nome, f.papel, f.icone) for f in FASES_CONCRETO.values()},
}

CHAVE_MODO = 'dados-modo'
ICONES_MODO = {'duas_fases': ':material/bubble_chart:', 'concreto': ':material/stacks:'}


def _estado_etapa(etapa: str, atual: str, liberadas: Iterable[str]) -> str:
    i, j = ETAPAS.index(etapa), ETAPAS.index(atual)
    if i == j:
        return 'atual'
    if etapa not in liberadas:
        return 'bloqueada'
    return 'concluida' if i < j else 'disponivel'


def descricao_padrao(etapa: str, modo: str = sessao.DUAS_FASES) -> str:
    """Descrição da etapa no ``modo`` ('duas_fases' ou 'concreto')."""
    if modo == sessao.CONCRETO and etapa in DESCRICOES_CONCRETO:
        return DESCRICOES_CONCRETO[etapa]
    return ETAPAS_INFO[etapa].descricao


def _descricao_etapa(etapa: str, estado: str, resumos: Dict[str, str], modo: str) -> str:
    if estado == 'bloqueada':
        return 'Disponível depois de calcular'
    return resumos.get(etapa) or descricao_padrao(etapa, modo)


def marca() -> None:
    """Marca HOOP com o nome do app."""
    st.html(f'<div class="hoop-marca">{GLIFOS["marca"]}'
            '<div><b>HOOP</b><small>Homogeneização de compósitos</small></div></div>')


def mapa_de_etapas(etapa_atual: str, liberadas: Iterable[str],
                   resumos: Optional[Dict[str, str]] = None,
                   modo: str = sessao.DUAS_FASES) -> None:
    """Sequence Map na barra lateral: marca, as 3 etapas e a versão.

    ``liberadas`` vem de ``estado.etapas_liberadas()``; ``resumos`` troca a
    descrição de uma etapa (ex.: {'dados': 'Concreto · esfera · 5 modelos'});
    ``modo`` escolhe as descrições padrão (as do concreto não falam de curvas).
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
                st.caption(_descricao_etapa(etapa, estado, resumos, modo))
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


def _ao_trocar_modo() -> None:
    sessao.definir_modo(st.session_state[CHAVE_MODO])


def seletor_modo() -> None:
    """Segmented control "Duas fases | Concreto multiescala" no topo da etapa Dados."""
    st.session_state.setdefault(CHAVE_MODO, sessao.modo_atual())
    st.segmented_control('Tipo de compósito', options=list(MODOS), key=CHAVE_MODO,
                         required=True, on_change=_ao_trocar_modo,
                         format_func=lambda m: f'{ICONES_MODO[m]} {MODOS[m]}')


def titulo_secao(icone: str, texto: str, detalhe: Optional[str] = None) -> None:
    """Título de seção com ícone Material (ex.: ``'science'``) e detalhe em cinza."""
    extra = f' <span class="hoop-mudo" style="font-size:13px">{escape(detalhe)}</span>' if detalhe else ''
    st.markdown(f'#### :material/{icone}: {escape(texto)}{extra}', unsafe_allow_html=True)


def rotulo_fase(fase: str, texto: str) -> str:
    """HTML do texto na cor da fase ('matriz', 'inclusao' ou uma chave de ``tema.CORES_FASE``)."""
    return f'<span class="hoop-fase hoop-fase-{fase}">{escape(texto)}</span>'


def titulo_fase(fase: str) -> None:
    """Cabeçalho do PhaseCard: quadrado na cor da fase, ícone, nome e papel da fase.

    ``fase`` é 'matriz', 'inclusao' ou uma chave de ``hoop.ui.concreto.FASES_CONCRETO``.
    """
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


def aviso_dados_alterados(chave: str = 'recalcular') -> bool:
    """Se a entrada mudou desde o cálculo, avisa e oferece "Recalcular".

    Devolve True quando "Recalcular" é clicado; a tela chama ``acoes.recalcular``.
    """
    if not sessao.dados_mudaram():
        return False
    texto, acao = st.columns([4, 1], vertical_alignment='center')
    texto.info('Os dados mudaram desde o último cálculo.', icon=':material/info:')
    return acao.button('Recalcular', icon=':material/refresh:', key=chave)
