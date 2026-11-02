"""Etapa 2: análise das curvas.

Center Stage com o gráfico de comparação, três métricas em fi de leitura,
tabela de valores nesse fi (Overview plus Detail) e, recolhidos, os gráficos
por modelo (Small Multiples) e a tabela completa com CSV.
"""
from dataclasses import replace
from html import escape
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from ui import estado
from ui.calculo import GRANDEZAS, LIMITES, ResultadoAnalise, fracoes, valor_em
from ui.componentes import aviso_dados_alterados, cabecalho, estado_vazio, rotulo_fase
from ui.estado import (formatar_decimal, formatar_numero, formatar_percentual,
                       interpretar_numero, rotulo_material)
from ui.graficos import figura_comparacao, figura_modelo_individual, limites_y
from ui.tema import SERIES

CHAVE_GRANDEZA = 'analise-grandeza'
CHAVE_FI = 'analise-fi'
CHAVE_COMPARAR = 'analise-comparar'

REFERENCIA_PADRAO = 'Mori-Tanaka'
TRIO = ('Mori-Tanaka', 'Self-Consistent', 'GSC')
ABREVIACOES = {'Mori-Tanaka': 'MT', 'Self-Consistent': 'SC', 'Dilute Suspension': 'Dilute'}
INCLUSOES = {'esfera': 'inclusões esféricas', 'cilindro': 'inclusões cilíndricas',
             'disco': 'inclusões em disco'}
SEM_VALOR = '—'
COLUNAS_SMALL_MULTIPLES = 3


def render() -> None:
    resultado = estado.resultado_atual()
    if resultado is None:
        cabecalho(2, 'Análise')
        estado_vazio('Ainda não há curvas para mostrar',
                     'Defina a matriz, a inclusão e os modelos. '
                     'O gráfico aparece aqui depois do cálculo.')
        return
    _preencher_controles(resultado.entrada.fi_max)
    grandeza = st.session_state[CHAVE_GRANDEZA]
    _cabecalho(resultado, grandeza)
    _avisos(resultado)
    if not resultado.calculados:
        return
    grandeza, fi = _controles(resultado)
    referencia = _referencia(resultado, st.session_state.get(CHAVE_COMPARAR))
    _metricas(resultado, grandeza, fi, referencia)
    _centro(resultado, grandeza, fi, referencia)
    _detalhes(resultado, grandeza)


def _cabecalho(resultado: ResultadoAnalise, grandeza: str) -> None:
    acoes = cabecalho(2, GRANDEZAS[grandeza].titulo, _subtitulo(resultado.entrada))
    with acoes.container(horizontal=True, horizontal_alignment='right'):
        st.button('Editar dados', icon=':material/edit:', key='analise-editar',
                  on_click=estado.ir_para, args=('dados',))
        st.button('Gerar relatório', icon=':material/picture_as_pdf:', type='primary',
                  key='analise-relatorio', on_click=estado.ir_para, args=('relatorio',))


def _subtitulo(entrada) -> str:
    matriz = f'Em {formatar_numero(entrada.Em)} MPa, νm {formatar_decimal(entrada.vm)}'
    inclusao = f'Ei {formatar_numero(entrada.Ei)} MPa, νi {formatar_decimal(entrada.vi)}'
    geometria = INCLUSOES.get(entrada.geometria, entrada.geometria)
    return ' · '.join((escape(rotulo_material(entrada.material)),
                       rotulo_fase('matriz', matriz), rotulo_fase('inclusao', inclusao),
                       escape(geometria)))


def _avisos(resultado: ResultadoAnalise) -> None:
    aviso_dados_alterados()
    for nome, falha in resultado.falhas.items():
        st.error(_mensagem_falha(resultado, nome, falha), icon=':material/error:')
    for curva in resultado.curvas.values():
        if curva.fi_validade is not None and resultado.entrada.fi_max > curva.fi_validade:
            st.warning(f'**{curva.nome} vale até fi ≈ {formatar_decimal(curva.fi_validade)}**  \n'
                       'Acima disso a curva aparece tracejada e o valor não entra na '
                       'comparação entre modelos.', icon=':material/warning:')


def _mensagem_falha(resultado: ResultadoAnalise, nome: str, falha) -> str:
    outros = [n for n in resultado.calculados if n != nome]
    if resultado.curvas[nome].vazia:
        titulo = f'{nome} não foi calculado para estes dados'
    else:
        titulo = f'{nome} não foi calculado a partir de fi = {formatar_decimal(falha.fi)}'
    if not outros:
        seguimento = 'Nenhum outro modelo tem curva para mostrar. Revise os dados em Dados.'
    elif len(outros) == 1:
        seguimento = f'{outros[0]} foi calculado normalmente e aparece no gráfico.'
    else:
        seguimento = (f'Os outros {len(outros)} modelos foram calculados normalmente '
                      'e aparecem no gráfico.')
    return f'**{titulo}**  \n{falha.mensagem} {seguimento}'


def _preencher_controles(fi_max: float) -> None:
    """Restaura grandeza e fi da última leitura quando a tela volta a ser exibida."""
    leitura = estado.leitura_atual()
    st.session_state.setdefault(CHAVE_GRANDEZA, leitura.grandeza)
    st.session_state.setdefault(CHAVE_FI, formatar_decimal(min(leitura.fi, fi_max)))


def _guardar_grandeza() -> None:
    leitura = estado.leitura_atual()
    estado.definir_leitura(replace(leitura, grandeza=st.session_state[CHAVE_GRANDEZA]))


def _guardar_fi() -> None:
    fi = interpretar_numero(st.session_state[CHAVE_FI])
    if fi is not None and 0 <= fi <= 1:
        estado.definir_leitura(replace(estado.leitura_atual(), fi=fi))


def _controles(resultado: ResultadoAnalise) -> Tuple[str, Optional[float]]:
    grandeza_col, fi_col, _ = st.columns([2, 1, 2], vertical_alignment='bottom')
    with grandeza_col:
        grandeza = st.segmented_control(
            'Grandeza', list(GRANDEZAS), required=True, key=CHAVE_GRANDEZA,
            on_change=_guardar_grandeza, format_func=lambda g: GRANDEZAS[g].rotulo,
            label_visibility='collapsed')
    with fi_col:
        fi = _campo_fi(resultado.entrada.fi_max)
    return grandeza or 'Eh', fi


def _campo_fi(fi_max: float) -> Optional[float]:
    texto = st.text_input('Ler valores em fi =', key=CHAVE_FI, on_change=_guardar_fi,
                          help=f'Aceita vírgula ou ponto. Entre 0 e {formatar_decimal(fi_max)}.')
    fi = interpretar_numero(texto)
    if fi is None or not 0 <= fi <= fi_max + 1e-12:
        st.error(f'Informe fi entre 0 e {formatar_decimal(fi_max)}.', icon=':material/error:')
        return None
    return fi


def _comparaveis(resultado: ResultadoAnalise) -> List[str]:
    """Modelos com curva que não são limites: candidatos a referência."""
    return [n for n in resultado.calculados if n not in LIMITES]


def _referencia(resultado: ResultadoAnalise, escolhido: Optional[str]) -> Optional[str]:
    candidatos = [escolhido, REFERENCIA_PADRAO, *_comparaveis(resultado), *resultado.calculados]
    return next((n for n in candidatos if n in resultado.calculados), None)


def _formatar(valor: Optional[float], grandeza: str, com_unidade: bool = False) -> str:
    if valor is None:
        return SEM_VALOR
    info = GRANDEZAS[grandeza]
    texto = formatar_numero(valor, info.casas)
    return f'{texto} {info.unidade}' if com_unidade and info.unidade else texto


def _valor_da_matriz(resultado: ResultadoAnalise, grandeza: str) -> float:
    entrada = resultado.entrada
    return {'Eh': entrada.Em, 'Eh/Em': 1.0, 'vh': entrada.vm}[grandeza]


def _valido(resultado: ResultadoAnalise, nome: str, grandeza: str, fi: float
            ) -> Optional[float]:
    """Valor do modelo em fi, ou None se não chegou a fi ou está fora da validade."""
    curva = resultado.curvas.get(nome)
    if curva is None or not curva.valido_em(fi):
        return None
    return valor_em(resultado, nome, grandeza, fi)


def _metricas(resultado: ResultadoAnalise, grandeza: str, fi: Optional[float],
              referencia: Optional[str]) -> None:
    colunas = st.columns(3)
    if fi is None:
        for coluna, rotulo in zip(colunas, ('Modelo de referência', 'Faixa Voigt–Reuss',
                                            'Diferença entre modelos')):
            coluna.metric(rotulo, SEM_VALOR, border=True)
        return
    _metrica_referencia(colunas[0], resultado, grandeza, fi, referencia)
    _metrica_faixa(colunas[1], resultado, grandeza, fi)
    _metrica_diferenca(colunas[2], resultado, grandeza, fi, referencia)


def _metrica_referencia(coluna, resultado, grandeza, fi, referencia) -> None:
    rotulo = f'{referencia} em fi {formatar_decimal(fi)}'
    valor = _valido(resultado, referencia, grandeza, fi)
    if valor is None:
        coluna.metric(rotulo, SEM_VALOR, border=True,
                      help='O modelo não tem valor válido neste fi.')
        return
    matriz = _valor_da_matriz(resultado, grandeza)
    relativo = (valor - matriz) / matriz
    lado = 'acima da matriz' if relativo >= 0 else 'abaixo da matriz'
    coluna.metric(rotulo, _formatar(valor, grandeza, com_unidade=True),
                  delta=formatar_percentual(abs(relativo)), delta_description=lado,
                  delta_color='off', delta_arrow='up' if relativo >= 0 else 'down',
                  border=True)


def _faixa(resultado: ResultadoAnalise, grandeza: str, fi: float
           ) -> Optional[Tuple[float, float]]:
    valores = [valor_em(resultado, n, grandeza, fi) for n in LIMITES]
    if None in valores:
        return None
    return min(valores), max(valores)


def _metrica_faixa(coluna, resultado, grandeza, fi) -> None:
    rotulo = f'Faixa Voigt–Reuss em fi {formatar_decimal(fi)}'
    faixa = _faixa(resultado, grandeza, fi)
    if faixa is None:
        coluna.metric(rotulo, SEM_VALOR, border=True,
                      help='Selecione Voigt e Reuss em Dados para ver a faixa.')
        return
    inf, sup = faixa
    coluna.metric(rotulo, f'{_formatar(inf, grandeza)}–{_formatar(sup, grandeza)}',
                  delta=f'Amplitude de {_formatar(sup - inf, grandeza, com_unidade=True)}',
                  delta_color='off', delta_arrow='off', border=True)


def _grupo_diferenca(resultado, grandeza, fi) -> Dict[str, float]:
    """Valores do trio MT, SC e GSC; sem dois deles, os demais modelos não-limite."""
    for grupo in (TRIO, _comparaveis(resultado)):
        valores = {n: _valido(resultado, n, grandeza, fi) for n in grupo}
        valores = {n: v for n, v in valores.items() if v is not None}
        if len(valores) >= 2:
            return valores
    return {}


def _juntar_nomes(nomes: List[str]) -> str:
    curtos = [ABREVIACOES.get(n, n) for n in nomes]
    return ', '.join(curtos[:-1]) + ' e ' + curtos[-1]


def _metrica_diferenca(coluna, resultado, grandeza, fi, referencia) -> None:
    valores = _grupo_diferenca(resultado, grandeza, fi)
    if not valores:
        coluna.metric('Diferença entre modelos', SEM_VALOR, border=True,
                      help='Selecione ao menos dois modelos além de Voigt e Reuss.')
        return
    diferenca = max(valores.values()) - min(valores.values())
    base_nome = referencia if referencia in valores else next(iter(valores))
    delta = (f'{formatar_percentual(diferenca / abs(valores[base_nome]))} '
             f'do valor de {base_nome}')
    coluna.metric(f'Diferença entre {_juntar_nomes(list(valores))}',
                  _formatar(diferenca, grandeza, com_unidade=True),
                  delta=delta, delta_color='off', delta_arrow='off', border=True)


def _centro(resultado: ResultadoAnalise, grandeza: str, fi: Optional[float],
            referencia: Optional[str]) -> None:
    grafico, tabela = st.columns([2, 1])
    with grafico.container(border=True):
        fig = figura_comparacao(resultado, grandeza, fi_leitura=fi, referencia=referencia)
        st.pyplot(fig, width='stretch')
        plt.close(fig)
    with tabela.container(border=True):
        _tabela_no_fi(resultado, grandeza, fi, referencia)


def _tabela_no_fi(resultado, grandeza, fi, referencia) -> None:
    if fi is None:
        st.markdown('**Valores em fi**')
        st.caption('Informe um fi válido para ver os valores.')
        return
    st.markdown(f'**Valores em fi = {formatar_decimal(fi)}**')
    st.dataframe(colorir_modelos(tabela_em_fi(resultado, grandeza, fi, referencia)),
                 hide_index=True, width='stretch')
    opcoes = _comparaveis(resultado) or list(resultado.calculados)
    padrao = REFERENCIA_PADRAO if REFERENCIA_PADRAO in opcoes else opcoes[0]
    st.segmented_control('Comparar com', opcoes, default=padrao, key=CHAVE_COMPARAR)


def tabela_em_fi(resultado: ResultadoAnalise, grandeza: str, fi: float,
                 referencia: Optional[str]) -> pd.DataFrame:
    """Linhas por modelo, em ordem decrescente de valor, com a diferença sobre a referência."""
    base = _valido(resultado, referencia, grandeza, fi) if referencia else None
    linhas = [_linha(resultado, nome, grandeza, fi, referencia, base)
              for nome in resultado.curvas]
    linhas.sort(key=lambda l: (l[0] is None, -(l[0] or 0)))
    coluna_vs = f'vs {ABREVIACOES.get(referencia, referencia)}' if referencia else 'vs'
    return pd.DataFrame([linha[1:] for linha in linhas],
                        columns=['Modelo', GRANDEZAS[grandeza].rotulo, coluna_vs])


def colorir_modelos(tabela: pd.DataFrame):
    """Styler que pinta o nome de cada modelo com a cor da sua série no gráfico."""
    return tabela.style.map(lambda nome: f'color: {SERIES[nome]}; font-weight: 600',
                            subset=['Modelo'])


def _linha(resultado, nome, grandeza, fi, referencia, base) -> Tuple:
    valor = valor_em(resultado, nome, grandeza, fi)
    if valor is None:
        return None, nome, SEM_VALOR, 'não calculado'
    if not resultado.curvas[nome].valido_em(fi):
        return valor, nome, _formatar(valor, grandeza), 'fora da validade'
    if nome == referencia:
        comparacao = 'ref.'
    elif base:
        comparacao = formatar_percentual((valor - base) / abs(base), sinal=True)
    else:
        comparacao = SEM_VALOR
    return valor, nome, _formatar(valor, grandeza), comparacao


def _detalhes(resultado: ResultadoAnalise, grandeza: str) -> None:
    nomes = list(resultado.calculados)
    with st.expander('Ver cada modelo em um gráfico próprio', icon=':material/grid_view:'):
        st.caption(f'{len(nomes)} gráficos na mesma escala')
        _small_multiples(resultado, nomes, grandeza)
    with st.expander('Tabela completa', icon=':material/table_chart:'):
        _tabela_completa(resultado, grandeza)


def _small_multiples(resultado: ResultadoAnalise, nomes: List[str], grandeza: str) -> None:
    limites = limites_y(resultado, grandeza)
    for inicio in range(0, len(nomes), COLUNAS_SMALL_MULTIPLES):
        colunas = st.columns(COLUNAS_SMALL_MULTIPLES)
        for coluna, nome in zip(colunas, nomes[inicio:inicio + COLUNAS_SMALL_MULTIPLES]):
            fig = figura_modelo_individual(resultado, nome, grandeza, limites)
            coluna.pyplot(fig, width='stretch')
            plt.close(fig)


def tabela_completa(resultado: ResultadoAnalise, grandeza: str) -> pd.DataFrame:
    """Uma linha por fi e uma coluna por modelo; NaN onde o modelo não chegou."""
    fis = fracoes(resultado.entrada.fi_max)
    dados = {'fi': fis}
    for nome, curva in resultado.curvas.items():
        coluna = np.full(len(fis), np.nan)
        coluna[:len(curva.fis)] = curva.valores[grandeza]
        dados[nome] = coluna
    return pd.DataFrame(dados)


def csv_pt_br(tabela: pd.DataFrame) -> bytes:
    """CSV com ponto e vírgula e vírgula decimal, que abre direto em planilhas pt-BR."""
    return tabela.to_csv(index=False, sep=';', decimal=',').encode('utf-8')


def formatar_tabela_completa(tabela: pd.DataFrame, casas: int):
    """Styler com vírgula decimal e espaço de milhar; travessão onde o modelo não chegou."""
    modelos = [c for c in tabela.columns if c != 'fi']
    return (tabela.style
            .format(formatar_decimal, subset=['fi'])
            .format(lambda v: formatar_numero(v, casas), subset=modelos, na_rep=SEM_VALOR))


def _tabela_completa(resultado: ResultadoAnalise, grandeza: str) -> None:
    tabela = tabela_completa(resultado, grandeza)
    info = GRANDEZAS[grandeza]
    st.caption(f'{len(tabela)} valores de fi × {len(resultado.curvas)} modelos · '
               f'{info.rotulo} · pode ser baixada em CSV')
    st.dataframe(formatar_tabela_completa(tabela, info.casas), hide_index=True,
                 width='stretch', height=320)
    st.download_button('Baixar CSV', csv_pt_br(tabela), file_name=_nome_csv(resultado, grandeza),
                       mime='text/csv', icon=':material/download:', key='analise-csv')


def _nome_csv(resultado: ResultadoAnalise, grandeza: str) -> str:
    sufixo = {'Eh': 'eh', 'Eh/Em': 'eh-em', 'vh': 'vh'}[grandeza]
    entrada = resultado.entrada
    return f'hoop-{entrada.material}-{entrada.geometria}-{sufixo}.csv'
