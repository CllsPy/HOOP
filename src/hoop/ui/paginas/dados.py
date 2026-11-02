"""Etapa 1: dados do compósito.

Os widgets guardam o texto digitado em ``st.session_state`` (chaves ``dados-*``);
``entrada_atual()`` é a fonte da verdade. Cada edição relê os widgets e grava
uma nova ``EntradaComposito``; preset e "Restaurar padrão" fazem o caminho
inverso e reescrevem os widgets.
"""
from dataclasses import replace
from decimal import Decimal
from typing import Dict, Optional

import streamlit as st

from hoop.ui.acoes import calcular_e_registrar
from hoop.ui.calculo import MODELOS, fracoes
from hoop.ui.componentes import cabecalho, amostra_serie, titulo_fase, titulo_secao
from hoop.ui.entrada import (GEOMETRIAS, GEOMETRIAS_DISPONIVEIS, PERSONALIZADO, PRESETS,
                             TIPOS_ANALISE, TIPOS_DISPONIVEIS, EntradaComposito, aplicar_preset,
                             preset_correspondente, resumo_entrada, rotulo_material, validar)
from hoop.ui.estado import definir_entrada, entrada_atual
from hoop.ui.formatacao import formatar_decimal, interpretar_numero

CHAVE_PRESET = 'dados-preset'
CHAVE_GEOMETRIA = 'dados-geometria'
CHAVE_TIPO = 'dados-tipo'
CHAVE_FI_MAX = 'dados-fi_max'
CHAVE_CALCULAR = 'dados-calcular'
CHAVE_RESTAURAR = 'dados-restaurar'

CAMPOS_FASE = {
    'matriz': (('Em', 'Módulo de Young Em [MPa]'), ('vm', 'Coeficiente de Poisson νm')),
    'inclusao': (('Ei', 'Módulo de Young Ei [MPa]'), ('vi', 'Coeficiente de Poisson νi')),
}
CAMPOS_POISSON = ('vm', 'vi')
DICA_POISSON = 'Entre 0 e 0,5. Aceita vírgula ou ponto.'
ERRO_TEXTO = 'Digite um número, como 30 000 ou 0,3.'

ICONES_TIPO = {'mecanica': ':material/compress:', 'condutividade': ':material/thermostat:'}
FAMILIAS = ('Limites', 'Campo médio', 'Autoconsistentes', 'Média')


def chave_campo(campo: str) -> str:
    return f'dados-{campo}'


def chave_modelo(nome: str) -> str:
    return f'dados-modelo-{nome}'


def texto_campo(valor: float, casas_minimas: int = 0) -> str:
    """Valor de campo em pt-BR sem perder casas: 30000 -> "30 000", 1e-7 -> "0,0000001"."""
    expoente = Decimal(repr(valor)).normalize().as_tuple().exponent
    casas = max(casas_minimas, -expoente)
    return f'{valor:,.{casas}f}'.replace(',', ' ').replace('.', ',')


def _valores_widgets(entrada: EntradaComposito) -> Dict[str, object]:
    valores = {chave_campo(c): texto_campo(getattr(entrada, c), 2 if c in CAMPOS_POISSON else 0)
               for campos in CAMPOS_FASE.values() for c, _ in campos}
    valores.update({chave_modelo(nome): nome in entrada.modelos for nome in MODELOS})
    valores.update({CHAVE_PRESET: entrada.material, CHAVE_GEOMETRIA: entrada.geometria,
                    CHAVE_TIPO: entrada.tipo_analise, CHAVE_FI_MAX: entrada.fi_max})
    return valores


def escrever_widgets(entrada: EntradaComposito, sobrescrever: bool = True) -> None:
    """Copia a entrada para os widgets; sem ``sobrescrever``, só preenche os que faltam."""
    for chave, valor in _valores_widgets(entrada).items():
        if sobrescrever or chave not in st.session_state:
            st.session_state[chave] = valor


def ler_widgets(entrada: EntradaComposito) -> EntradaComposito:
    """Nova entrada a partir dos widgets; texto que não é número mantém o valor anterior."""
    estado = st.session_state
    numeros = {c: interpretar_numero(estado[chave_campo(c)])
               for campos in CAMPOS_FASE.values() for c, _ in campos}
    nova = replace(
        entrada,
        **{c: v for c, v in numeros.items() if v is not None},
        modelos=tuple(nome for nome in MODELOS if estado[chave_modelo(nome)]),
        geometria=estado[CHAVE_GEOMETRIA],
        tipo_analise=estado[CHAVE_TIPO],
        fi_max=float(estado[CHAVE_FI_MAX]),
    )
    return replace(nova, material=preset_correspondente(nova))


def ao_editar() -> None:
    entrada = ler_widgets(entrada_atual())
    definir_entrada(entrada)
    st.session_state[CHAVE_PRESET] = entrada.material


def ao_escolher_preset() -> None:
    entrada, chave = entrada_atual(), st.session_state[CHAVE_PRESET]
    if chave in PRESETS:
        entrada = aplicar_preset(entrada, chave)
    elif chave == PERSONALIZADO:
        entrada = replace(entrada, material=PERSONALIZADO)
    definir_entrada(entrada)
    escrever_widgets(entrada)


def restaurar_padrao() -> None:
    definir_entrada(EntradaComposito())
    escrever_widgets(EntradaComposito())


def erros_de_texto() -> Dict[str, str]:
    return {c: ERRO_TEXTO for campos in CAMPOS_FASE.values() for c, _ in campos
            if interpretar_numero(st.session_state[chave_campo(c)]) is None}


def erro_inline(mensagem: Optional[str]) -> None:
    if mensagem:
        st.error(mensagem, icon=':material/error:')


def secao_preset() -> None:
    titulo_secao('science', 'Ponto de partida')
    st.pills('Ponto de partida', options=[*PRESETS, PERSONALIZADO], format_func=rotulo_material,
             key=CHAVE_PRESET, on_change=ao_escolher_preset, required=True,
             label_visibility='collapsed')
    st.caption('Valores típicos de literatura. Alterar qualquer campo muda o ponto de '
               'partida para Personalizado.')


def campo_fase(campo: str, rotulo: str, erros: Dict[str, str]) -> None:
    st.text_input(rotulo, key=chave_campo(campo), on_change=ao_editar)
    if campo in erros:
        erro_inline(erros[campo])
    elif campo in CAMPOS_POISSON:
        st.caption(DICA_POISSON)


def cartao_fase(fase: str, erros: Dict[str, str]) -> None:
    with st.container(border=True):
        titulo_fase(fase)
        for campo, rotulo in CAMPOS_FASE[fase]:
            campo_fase(campo, rotulo, erros)


def leitura_contraste(contraste: float) -> str:
    if contraste > 1:
        return 'Inclusão mais rígida que a matriz: Reuss é o limite inferior e Voigt o superior.'
    if contraste < 1:
        return ('Inclusão mais flexível que a matriz: o módulo cai com fi. '
                'Reuss continua o limite inferior e Voigt o superior.')
    return 'Fases com a mesma rigidez: todos os modelos dão o mesmo módulo.'


def contraste(entrada: EntradaComposito, erros: Dict[str, str]) -> None:
    if 'Em' in erros or 'Ei' in erros:
        return
    razao = entrada.Ei / entrada.Em
    st.markdown(f':material/compare_arrows: Contraste de rigidez '
                f'<span class="hoop-dado">Ei/Em = {formatar_decimal(razao)}</span>',
                unsafe_allow_html=True)
    st.caption(leitura_contraste(razao))


def _opcao(nome: str, icone: str = '') -> str:
    return f'{icone} {nome}'.strip()


def seletor_restrito(rotulo: str, chave: str, nomes: Dict[str, str], disponiveis,
                     aviso: str, icone_titulo: str = '', icones: Optional[Dict[str, str]] = None
                     ) -> None:
    """Segmented control com as opções disponíveis e, ao lado, as futuras desabilitadas."""
    futuras, icones = [k for k in nomes if k not in disponiveis], icones or {}
    st.markdown(f'**{_opcao(rotulo, icone_titulo)}**')
    ativas, inativas = st.columns([1, 2])
    ativas.segmented_control(rotulo, options=list(disponiveis), key=chave, on_change=ao_editar,
                             required=True,
                             format_func=lambda k: _opcao(nomes[k], icones.get(k, '')),
                             label_visibility='collapsed')
    inativas.segmented_control(f'{rotulo} ({aviso})', options=futuras, disabled=True,
                               key=f'{chave}-futuras', label_visibility='collapsed',
                               format_func=lambda k: _opcao(f'{nomes[k]} · {aviso}',
                                                                    icones.get(k, '')))


def secao_geometria_e_tipo() -> None:
    geometria, tipo = st.columns(2)
    with geometria:
        seletor_restrito('Geometria da inclusão', CHAVE_GEOMETRIA, GEOMETRIAS,
                         GEOMETRIAS_DISPONIVEIS, 'em validação', ':material/category:')
    with tipo:
        seletor_restrito('Tipo de análise', CHAVE_TIPO, TIPOS_ANALISE, TIPOS_DISPONIVEIS,
                         'em breve', icones=ICONES_TIPO)


def item_modelo(nome: str) -> None:
    st.checkbox(nome, key=chave_modelo(nome), on_change=ao_editar)
    st.markdown(f'{amostra_serie(nome)}<span class="hoop-mudo" style="font-size:13px">'
                f'{MODELOS[nome].descricao}</span>', unsafe_allow_html=True)


def secao_modelos(entrada: EntradaComposito, erros: Dict[str, str]) -> None:
    titulo_secao('function', 'Modelos a comparar',
                 f'{len(entrada.modelos)} de {len(MODELOS)} selecionados')
    for coluna, familia in zip(st.columns(len(FAMILIAS)), FAMILIAS):
        with coluna, st.container(border=True):
            st.html(f'<span class="hoop-sobretitulo">{familia}</span>')
            for nome, info in MODELOS.items():
                if info.familia == familia:
                    item_modelo(nome)
    erro_inline(erros.get('modelos'))


def secao_fracao(erros: Dict[str, str]) -> None:
    titulo_secao('percent', 'Fração volumétrica de inclusão')
    fi_max = st.slider('Calcular de fi = 0 até', min_value=0.01, max_value=1.0, step=0.01,
                       format='%.2f', key=CHAVE_FI_MAX, on_change=ao_editar)
    st.caption(f'{len(fracoes(fi_max))} pontos, passo 0,01')
    erro_inline(erros.get('fi_max'))


def texto_resumo(entrada: EntradaComposito, erros: Dict[str, str]) -> str:
    if erros:
        n = len(erros)
        return f':red[:material/error: {n} campo{"s" if n > 1 else ""} para corrigir]'
    return f'{resumo_entrada(entrada)} · fi 0 a {formatar_decimal(entrada.fi_max)}'


def barra_final(entrada: EntradaComposito, erros: Dict[str, str]) -> bool:
    """Resumo e ações; devolve True quando "Calcular" é clicado."""
    with st.container(border=True):
        resumo, restaurar, acao = st.columns([4, 1.3, 1], vertical_alignment='center')
        resumo.markdown(texto_resumo(entrada, erros))
        restaurar.button('Restaurar padrão', key=CHAVE_RESTAURAR, icon=':material/restart_alt:',
                         on_click=restaurar_padrao, width='stretch')
        return acao.button('Calcular', key=CHAVE_CALCULAR, type='primary',
                           icon=':material/calculate:', disabled=bool(erros),
                           width='stretch')


def render() -> None:
    entrada = entrada_atual()
    escrever_widgets(entrada, sobrescrever=False)
    erros = {**validar(entrada), **erros_de_texto()}

    cabecalho(1, 'Defina o compósito', 'Comece por um material conhecido ou digite as '
              'propriedades da matriz e da inclusão.')
    secao_preset()
    titulo_secao('layers', 'Fases')
    for coluna, fase in zip(st.columns(2), CAMPOS_FASE):
        with coluna:
            cartao_fase(fase, erros)
    contraste(entrada, erros)
    secao_geometria_e_tipo()
    secao_modelos(entrada, erros)
    secao_fracao(erros)
    if barra_final(entrada, erros):
        calcular_e_registrar(entrada, proxima_etapa='analise')
