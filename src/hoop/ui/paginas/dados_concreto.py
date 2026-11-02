"""Etapa 1 no modo "Concreto multiescala": fases, poros, construção e prévia dos níveis.

Mesmo padrão da etapa de duas fases: os widgets guardam o texto digitado
(chaves ``concreto-*``) e ``entrada_concreto_atual()`` é a fonte da verdade.
Cada edição relê os widgets; "Restaurar valores da tese" reescreve os widgets.
As escolhas (construção, modelos, modelo dos poros) são copiadas da entrada a
cada execução, e só para os widgets que serão desenhados: a chave de um
widget oculto sai do estado, para não voltar com um valor antigo.
"""
from dataclasses import replace
from html import escape
from typing import Dict, Optional, Set

import streamlit as st

from hoop.ui.acoes import calcular_concreto_e_registrar
from hoop.ui.calculo import MODELOS
from hoop.ui.componentes import (amostra_serie, cabecalho, seletor_modo, titulo_fase,
                                 titulo_secao)
from hoop.ui.concreto import (COM_ZTI, CONSTRUCOES, FASES_CONCRETO, MODELOS_POROS, MODELOS_ZTI,
                              POROS_MT, ZTIS, EntradaConcreto, PreviaNivel, PropriedadesFase,
                              eh_padrao_da_tese, poisson_poros_texto, previa_niveis,
                              restaurar_tese, resumo_concreto, soma_fracoes, validar_concreto)
from hoop.ui.estado import definir_entrada_concreto, entrada_concreto_atual
from hoop.ui.formatacao import formatar_numero, formatar_percentual, interpretar_numero
from hoop.ui.paginas.dados import FAMILIAS, erro_inline, texto_campo
from hoop.ui.tema import CORES_FASE

CHAVE_CONSTRUCAO = 'concreto-construcao'
CHAVE_POROS = 'concreto-poros'
CHAVE_E_EXP = 'concreto-E_exp'
CHAVE_MODELO_POROS = 'concreto-modelo-poros'
CHAVE_CALCULAR = 'concreto-calcular'
CHAVE_RESTAURAR = 'concreto-restaurar'

CAMPOS = (('E', 'Módulo de Young E [MPa]'), ('v', 'Coeficiente de Poisson ν'),
          ('fracao', 'Fração no concreto [%]'))
LINHAS_CARTOES = (('pasta', 'agregado_miudo', 'zti_miudo'), ('agregado_graudo', 'zti_graudo'))
ICONES_CONSTRUCAO = {COM_ZTI: ':material/blur_circular:', 'sem_zti': ':material/circle:'}
DESCRICAO_CONSTRUCAO = {
    COM_ZTI: 'Cada agregado entra revestido pela sua ZTI (modelos de três fases).',
    'sem_zti': ('Pasta e agregados com modelos de duas fases. As frações das ZTIs saem '
                'da conta e as demais são renormalizadas.'),
}
_CASAS_FRACAO = 10
ERROS_TEXTO = {'E': 'Digite um número, como 21 340.', 'v': 'Digite um número, como 0,25.',
               'fracao': 'Digite a fração em %, como 15,4.'}
ERRO_TEXTO_POROS = 'Digite a fração em %, como 2,42.'


def chave_campo(fase: str, campo: str) -> str:
    return f'concreto-{fase}-{campo}'


def chave_modelo(nome: str) -> str:
    return f'concreto-modelo-{nome}'


def _texto_fracao(fracao: float) -> str:
    return texto_campo(round(fracao * 100, 6), 1)


def _textos_widgets(entrada: EntradaConcreto) -> Dict[str, str]:
    """Texto dos campos numéricos (sempre visíveis na etapa)."""
    valores: Dict[str, str] = {}
    for chave in FASES_CONCRETO:
        fase = entrada.fase(chave)
        valores[chave_campo(chave, 'E')] = texto_campo(fase.E)
        valores[chave_campo(chave, 'v')] = texto_campo(fase.v, 2)
        valores[chave_campo(chave, 'fracao')] = _texto_fracao(fase.fracao)
    valores[CHAVE_POROS] = _texto_fracao(entrada.poros)
    valores[CHAVE_E_EXP] = ('' if entrada.E_experimental is None
                            else texto_campo(entrada.E_experimental))
    return valores


def mostra_modelo_poros(entrada: EntradaConcreto) -> bool:
    """O seletor "Modelo dos poros" só aparece sem ZTI e com poros."""
    return not entrada.com_zti and entrada.poros > 0


def _escolhas_widgets(entrada: EntradaConcreto) -> Dict[str, object]:
    """Valor de cada widget de escolha, inclusive os que esta execução não desenha."""
    valores: Dict[str, object] = {CHAVE_CONSTRUCAO: entrada.construcao,
                                  CHAVE_MODELO_POROS: entrada.modelo_poros}
    valores.update({chave_modelo(n): n in entrada.modelos_zti for n in MODELOS_ZTI})
    valores.update({chave_modelo(n): n in entrada.modelos_sem_zti for n in MODELOS})
    return valores


def escolhas_visiveis(entrada: EntradaConcreto) -> Set[str]:
    """Chaves dos widgets de escolha que a etapa desenha para ``entrada``."""
    catalogo = MODELOS_ZTI if entrada.com_zti else MODELOS
    visiveis = {CHAVE_CONSTRUCAO, *(chave_modelo(n) for n in catalogo)}
    if mostra_modelo_poros(entrada):
        visiveis.add(CHAVE_MODELO_POROS)
    return visiveis


def escrever_widgets(entrada: EntradaConcreto, sobrescrever: bool = True) -> None:
    """Copia a entrada para os widgets.

    As escolhas visíveis sempre recebem o valor da entrada e as ocultas saem
    do estado. Os textos só são reescritos com ``sobrescrever``; sem ele, só
    os que faltam, para não apagar um texto inválido que o usuário corrige.
    """
    estado = st.session_state
    for chave, valor in _textos_widgets(entrada).items():
        if sobrescrever or chave not in estado:
            estado[chave] = valor
    visiveis = escolhas_visiveis(entrada)
    for chave, valor in _escolhas_widgets(entrada).items():
        if chave in visiveis:
            estado[chave] = valor
        else:
            estado.pop(chave, None)


def _e_fracao(chave: str) -> bool:
    return chave == CHAVE_POROS or chave.endswith('-fracao')


def numero_digitado(chave: str) -> Optional[float]:
    """Número do campo ``chave``; nos campos de fração aceita um "%" no fim (15,4%)."""
    texto = str(st.session_state.get(chave, '')).strip()
    if _e_fracao(chave) and texto.endswith('%'):
        texto = texto[:-1]
    return interpretar_numero(texto)


def _ler_numero(chave: str, anterior: float, escala: float = 1.0) -> float:
    valor = numero_digitado(chave)
    return anterior if valor is None else round(valor / escala, _CASAS_FRACAO)


def _ler_fase(entrada: EntradaConcreto, chave: str) -> PropriedadesFase:
    fase = entrada.fase(chave)
    return PropriedadesFase(E=_ler_numero(chave_campo(chave, 'E'), fase.E),
                            v=_ler_numero(chave_campo(chave, 'v'), fase.v),
                            fracao=_ler_numero(chave_campo(chave, 'fracao'), fase.fracao, 100))


def _ler_E_experimental(anterior: Optional[float]) -> Optional[float]:
    texto = str(st.session_state.get(CHAVE_E_EXP, '')).strip()
    if not texto:
        return None
    valor = interpretar_numero(texto)
    return anterior if valor is None else valor


def _ler_modelos(catalogo, anteriores, visivel: bool):
    if not visivel:
        return anteriores
    estado = st.session_state
    return tuple(n for n in catalogo if estado.get(chave_modelo(n), n in anteriores))


def ler_widgets(entrada: EntradaConcreto) -> EntradaConcreto:
    """Nova entrada a partir dos widgets; texto que não é número mantém o valor anterior.

    Só lê as escolhas que estavam na tela (as de ``entrada``); as outras
    ficam como estão na entrada.
    """
    estado = st.session_state
    visiveis = escolhas_visiveis(entrada)
    modelo_poros = (estado.get(CHAVE_MODELO_POROS) if CHAVE_MODELO_POROS in visiveis
                    else None) or entrada.modelo_poros
    return replace(
        entrada,
        **{c: _ler_fase(entrada, c) for c in FASES_CONCRETO},
        poros=_ler_numero(CHAVE_POROS, entrada.poros, 100),
        E_experimental=_ler_E_experimental(entrada.E_experimental),
        construcao=estado.get(CHAVE_CONSTRUCAO) or entrada.construcao,
        modelo_poros=modelo_poros,
        modelos_zti=_ler_modelos(MODELOS_ZTI, entrada.modelos_zti, entrada.com_zti),
        modelos_sem_zti=_ler_modelos(MODELOS, entrada.modelos_sem_zti, not entrada.com_zti),
    )


def ao_editar() -> None:
    definir_entrada_concreto(ler_widgets(entrada_concreto_atual()))


def restaurar_valores_da_tese() -> None:
    entrada = restaurar_tese(entrada_concreto_atual())
    definir_entrada_concreto(entrada)
    escrever_widgets(entrada)


def erros_de_texto() -> Dict[str, str]:
    erros = {f'{fase}.{campo}': ERROS_TEXTO[campo] for fase in FASES_CONCRETO
             for campo, _ in CAMPOS if numero_digitado(chave_campo(fase, campo)) is None}
    if numero_digitado(CHAVE_POROS) is None:
        erros['poros'] = ERRO_TEXTO_POROS
    texto_exp = str(st.session_state.get(CHAVE_E_EXP, '')).strip()
    if texto_exp and interpretar_numero(texto_exp) is None:
        erros['E_experimental'] = 'Digite um número, como 34 500, ou deixe vazio.'
    return erros


# --- Seções ------------------------------------------------------------------

def campo(fase: str, nome: str, rotulo: str, erros: Dict[str, str]) -> None:
    st.text_input(rotulo, key=chave_campo(fase, nome), on_change=ao_editar)
    erro_inline(erros.get(f'{fase}.{nome}'))


def cartao_fase(entrada: EntradaConcreto, fase: str, erros: Dict[str, str]) -> None:
    with st.container(border=True):
        titulo_fase(fase)
        for nome, rotulo in CAMPOS:
            campo(fase, nome, rotulo, erros)
        if fase in ZTIS and not entrada.com_zti:
            st.caption(':material/info: Sem ZTI esta fase fica de fora do cálculo; '
                       'a fração ainda conta na soma de 100%.')


def cartao_poros(erros: Dict[str, str]) -> None:
    with st.container(border=True):
        st.markdown(
            f'#### <span class="hoop-quadrado" style="background:{CORES_FASE["poros"]}" '
            'aria-hidden="true"></span>:material/blur_on: Poros '
            '<span class="hoop-mudo" style="font-size:13px;font-weight:400">vazios</span>',
            unsafe_allow_html=True)
        st.text_input('Poros em relação aos sólidos [%]', key=CHAVE_POROS, on_change=ao_editar)
        erro_inline(erros.get('poros'))
        st.caption(f'Entram no nível 3 como vazios (E = 0, ν = {poisson_poros_texto()}). '
                   'Use 0 para parar no nível 2.')


def secao_fases(entrada: EntradaConcreto, erros: Dict[str, str]) -> None:
    titulo_secao('layers', 'Fases', 'frações no concreto; as cinco somam 100%')
    for linha in LINHAS_CARTOES:
        colunas = st.columns(3)
        for coluna, fase in zip(colunas, linha):
            with coluna:
                cartao_fase(entrada, fase, erros)
    with colunas[2]:
        cartao_poros(erros)
    if 'soma' in erros:
        erro_inline(erros['soma'])
    elif not any(k.endswith('.fracao') for k in erros):
        st.markdown(f':material/check_circle: Soma das frações sólidas '
                    f'<span class="hoop-dado">{formatar_percentual(soma_fracoes(entrada), 2)}'
                    '</span>', unsafe_allow_html=True)


def item_modelo(nome: str, descricao: str) -> None:
    st.checkbox(nome, key=chave_modelo(nome), on_change=ao_editar)
    st.markdown(f'{amostra_serie(nome)}<span class="hoop-mudo" style="font-size:13px">'
                f'{escape(descricao)}</span>', unsafe_allow_html=True)


def _modelos_com_zti() -> None:
    for coluna, (nome, info) in zip(st.columns(2), MODELOS_ZTI.items()):
        with coluna:
            item_modelo(nome, info.descricao)
    st.caption('Os poros entram no nível 3 por Mori-Tanaka, como na tese.')


def _modelos_sem_zti(entrada: EntradaConcreto) -> None:
    for coluna, familia in zip(st.columns(len(FAMILIAS)), FAMILIAS):
        with coluna:
            st.html(f'<span class="hoop-sobretitulo">{familia}</span>')
            for nome, info in MODELOS.items():
                if info.familia == familia:
                    item_modelo(nome, info.descricao)
    if mostra_modelo_poros(entrada):
        st.segmented_control('Modelo dos poros (nível 3)', options=list(MODELOS_POROS),
                             key=CHAVE_MODELO_POROS, on_change=ao_editar, required=True,
                             format_func=MODELOS_POROS.get)
        if entrada.modelo_poros != POROS_MT:
            st.caption('Reuss e Popovic não se aplicam a vazios: com essa opção eles param '
                       'no nível 2.')


def secao_construcao(entrada: EntradaConcreto, erros: Dict[str, str]) -> None:
    n, total = len(entrada.modelos), len(MODELOS_ZTI if entrada.com_zti else MODELOS)
    titulo_secao('function', 'Construção e modelos', f'{n} de {total} selecionados')
    with st.container(border=True):
        st.segmented_control('Construção', options=list(CONSTRUCOES), key=CHAVE_CONSTRUCAO,
                             on_change=ao_editar, required=True, label_visibility='collapsed',
                             format_func=lambda c: f'{ICONES_CONSTRUCAO[c]} {CONSTRUCOES[c]}')
        st.caption(DESCRICAO_CONSTRUCAO[entrada.construcao])
        if entrada.com_zti:
            _modelos_com_zti()
        else:
            _modelos_sem_zti(entrada)
        erro_inline(erros.get('modelos'))


def secao_referencia(erros: Dict[str, str]) -> None:
    titulo_secao('science', 'Referência experimental')
    with st.container(border=True):
        st.text_input('E experimental [MPa]', key=CHAVE_E_EXP, on_change=ao_editar,
                      placeholder='Opcional')
        erro_inline(erros.get('E_experimental'))
        st.caption('Opcional. Com ele, a Análise mostra o erro do E do concreto. '
                   'Li et al. (2019) mediram 34 500 MPa.')


def _html_nivel(nivel: PreviaNivel) -> str:
    barra = ''.join(f'<span style="width:{f.fracao * 100:.4f}%;background:{CORES_FASE[f.chave]}">'
                    '</span>' for f in nivel.fases if f.fracao > 0)
    linhas = ''.join(
        f'<div class="hoop-nivel-linha"><span class="hoop-fase hoop-fase-{f.chave}">'
        f'<span class="hoop-quadrado" style="background:{CORES_FASE[f.chave]}"></span>'
        f'{escape(f.rotulo)}</span><span class="hoop-dado">{formatar_percentual(f.fracao, 2)}'
        '</span></div>' for f in nivel.fases)
    papel = 'matriz' if nivel.numero == 1 else 'homogeneizado do nível anterior'
    return (f'<div class="hoop-nivel" role="group" aria-label="Nível {nivel.numero}">'
            f'<div class="hoop-nivel-titulo">Nível {nivel.numero} · {escape(nivel.nome)}</div>'
            f'<div class="hoop-nivel-barra" aria-hidden="true">{barra}</div>{linhas}'
            f'<div class="hoop-mudo" style="font-size:13px;margin-top:4px">'
            f'{escape(nivel.fases[0].rotulo)}: {papel}</div></div>')


def html_previa(entrada: EntradaConcreto) -> str:
    """Diagrama dos níveis: uma caixa por nível com a barra das frações e os valores."""
    seta = '<span class="hoop-nivel-seta" aria-hidden="true">→</span>'
    return f'<div class="hoop-niveis">{seta.join(_html_nivel(n) for n in previa_niveis(entrada))}</div>'


def secao_previa(entrada: EntradaConcreto, erros: Dict[str, str]) -> None:
    niveis = len(previa_niveis(entrada)) if 'poros' not in erros else 2
    titulo_secao('account_tree', 'Níveis de homogeneização',
                 f'{niveis} níveis · frações corrigidas em cada nível')
    if any(k.endswith('.fracao') or k in ('soma', 'poros') for k in erros):
        st.caption('Corrija as frações para ver a prévia dos níveis.')
        return
    st.html(html_previa(entrada))


def texto_resumo(entrada: EntradaConcreto, erros: Dict[str, str]) -> str:
    if erros:
        n = len(erros)
        return f':red[:material/error: {n} campo{"s" if n > 1 else ""} para corrigir]'
    niveis = len(previa_niveis(entrada))
    partes = [resumo_concreto(entrada), f'{niveis} níveis']
    if entrada.E_experimental is not None:
        partes.append(f'E exp. {formatar_numero(entrada.E_experimental)} MPa')
    if eh_padrao_da_tese(entrada):
        partes.append('Li et al. (2019)')
    return ' · '.join(partes)


def barra_final(entrada: EntradaConcreto, erros: Dict[str, str]) -> bool:
    """Resumo e ações; devolve True quando "Calcular" é clicado."""
    with st.container(border=True):
        resumo, restaurar, acao = st.columns([4, 1.6, 1], vertical_alignment='center')
        resumo.markdown(texto_resumo(entrada, erros))
        restaurar.button('Restaurar valores da tese', key=CHAVE_RESTAURAR,
                         icon=':material/restart_alt:', on_click=restaurar_valores_da_tese,
                         help='Fases, poros e E experimental de Li et al. (2019). '
                              'A construção e os modelos ficam como estão.',
                         width='stretch')
        return acao.button('Calcular', key=CHAVE_CALCULAR, type='primary',
                           icon=':material/calculate:', disabled=bool(erros), width='stretch')


def render() -> None:
    entrada = entrada_concreto_atual()
    escrever_widgets(entrada, sobrescrever=False)
    erros = {**validar_concreto(entrada), **erros_de_texto()}

    cabecalho(1, 'Defina o concreto', 'Pasta, agregados e ZTIs homogeneizados em níveis. '
              'Os valores iniciais são de Li et al. (2019).')
    seletor_modo()
    secao_fases(entrada, erros)
    construcao, referencia = st.columns([2, 1])
    with construcao:
        secao_construcao(entrada, erros)
    with referencia:
        secao_referencia(erros)
    secao_previa(entrada, erros)
    if barra_final(entrada, erros):
        calcular_concreto_e_registrar(entrada, proxima_etapa='analise')
