"""Etapa 2 no modo "Concreto multiescala": E do concreto, erro e níveis.

Center Stage com o gráfico de E por nível e a tabela compacta (no estilo das
Tabelas 6 e 8 da tese); acima, três métricas; abaixo, as propriedades de cada
nível (E, ν, K, G) e as frações usadas.
"""
from html import escape
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from hoop.ui import estado
from hoop.ui.acoes import recalcular
from hoop.ui.componentes import aviso_dados_alterados, cabecalho, estado_vazio
from hoop.ui.concreto import (CONSTRUCOES_MINUSCULAS, ROTULOS_NIVEL, ResultadoConcreto,
                              aviso_validade, escolher_destaque)
from hoop.ui.formatacao import formatar_numero, formatar_percentual
from hoop.ui.graficos import figura_niveis
from hoop.ui.paginas.analise import SEM_VALOR, colorir_modelos, csv_pt_br
from hoop.ui.paginas.dados_concreto import html_previa

CHAVE_DESTAQUE = 'concreto-analise-destaque'
TITULO = 'Módulo de Young do concreto'


def render() -> None:
    resultado = estado.resultado_concreto_atual()
    if resultado is None:
        cabecalho(2, 'Análise')
        estado_vazio('Ainda não há níveis para mostrar',
                     'Defina as fases do concreto e os modelos. '
                     'O gráfico aparece aqui depois do cálculo.')
        return
    _cabecalho(resultado)
    _avisos(resultado)
    if not any(s.niveis for s in resultado.series.values()):
        return
    destaque = _destaque(resultado)
    _metricas(resultado, destaque)
    _centro(resultado, destaque)
    _detalhes(resultado)


def _cabecalho(resultado: ResultadoConcreto) -> None:
    acoes = cabecalho(2, TITULO, escape(subtitulo(resultado)))
    with acoes.container(horizontal=True, horizontal_alignment='right'):
        st.button('Editar dados', icon=':material/edit:', key='analise-editar',
                  on_click=estado.ir_para, args=('dados',))
        st.button('Gerar relatório', icon=':material/picture_as_pdf:', type='primary',
                  key='analise-relatorio', on_click=estado.ir_para, args=('relatorio',))


def subtitulo(resultado: ResultadoConcreto) -> str:
    """"Concreto multiescala · com ZTI · 3 níveis · poros 2,42%"."""
    e = resultado.entrada
    partes = ['Concreto multiescala', CONSTRUCOES_MINUSCULAS[e.construcao],
              f'{resultado.numero_niveis} níveis']
    if e.poros > 0:
        partes.append(f'poros {formatar_percentual(e.poros, 2)}')
    return ' · '.join(partes)


def _avisos(resultado: ResultadoConcreto) -> None:
    if aviso_dados_alterados():
        recalcular()
    for nome, falha in resultado.falhas.items():
        st.error(mensagem_falha(resultado, nome), icon=':material/error:')
    for nome in resultado.series:
        aviso = aviso_validade(resultado, nome)
        if aviso:
            st.warning(aviso, icon=':material/warning:')


def mensagem_falha(resultado: ResultadoConcreto, nome: str) -> str:
    """O que aconteceu (modelo e nível) e o que fazer, no padrão de Estados do DS."""
    falha = resultado.falhas[nome]
    outros = [n for n in resultado.calculados if n != nome]
    if falha.nivel:
        titulo = f'{nome} não foi calculado no nível {falha.nivel}'
        parcial = f' Os níveis 1 a {falha.nivel - 1} aparecem no gráfico.'
    else:
        titulo = f'{nome} não foi calculado para estes dados'
        parcial = ''
    if not outros:
        seguimento = 'Nenhum outro modelo chegou ao último nível. Revise os dados em Dados.'
    elif len(outros) == 1:
        seguimento = f'{outros[0]} foi calculado normalmente.'
    else:
        seguimento = f'Os outros {len(outros)} modelos foram calculados normalmente.'
    return f'**{titulo}**  \n{falha.mensagem}{parcial} {seguimento}'


def _ao_destacar() -> None:
    estado.definir_destaque_concreto(st.session_state.get(CHAVE_DESTAQUE))


def _destaque(resultado: ResultadoConcreto) -> Optional[str]:
    """Modelo destacado; a escolha fica no estado e vale também no PDF e na barra lateral."""
    destaque = escolher_destaque(resultado, estado.destaque_concreto_atual())
    opcoes = list(resultado.calculados)
    if len(opcoes) < 2:
        return destaque
    st.session_state[CHAVE_DESTAQUE] = destaque
    return st.segmented_control('Destacar modelo', opcoes, key=CHAVE_DESTAQUE,
                                required=True, on_change=_ao_destacar) or destaque


def _metricas(resultado: ResultadoConcreto, destaque: Optional[str]) -> None:
    colunas = st.columns(3)
    exp = resultado.entrada.E_experimental
    if destaque is None:
        colunas[0].metric('E do concreto', SEM_VALOR, border=True,
                          help='Nenhum modelo chegou ao último nível.')
        colunas[1].metric('Erro vs experimental', SEM_VALOR, border=True)
    else:
        serie = resultado.series[destaque]
        anterior = serie.niveis[-2].resultado.Eh if len(serie.niveis) > 1 else None
        variacao = (serie.Eh - anterior) / anterior if anterior else None
        colunas[0].metric(
            f'E do concreto · {destaque}', f'{formatar_numero(serie.Eh)} MPa',
            delta=formatar_percentual(abs(variacao)) if variacao is not None else None,
            delta_description=(('abaixo' if variacao < 0 else 'acima') + ' do nível anterior'
                               if variacao is not None else None),
            delta_color='off', delta_arrow='down' if (variacao or 0) < 0 else 'up', border=True)
        if exp is None:
            colunas[1].metric('Erro vs experimental', SEM_VALOR, border=True,
                              help='Informe o E experimental em Dados para ver o erro.')
        else:
            colunas[1].metric('Erro vs experimental',
                              formatar_percentual(serie.erro_relativo, 2, sinal=True),
                              delta=f'E experimental {formatar_numero(exp)} MPa',
                              delta_color='off', delta_arrow='off', border=True)
    _metrica_diferenca(colunas[2], resultado)


def _metrica_diferenca(coluna, resultado: ResultadoConcreto) -> None:
    valores = {n: resultado.series[n].Eh for n in resultado.calculados}
    if len(valores) < 2:
        coluna.metric('Níveis calculados', str(resultado.numero_niveis), border=True,
                      delta=' → '.join(r.split(' · ')[1] for r in
                                       ROTULOS_NIVEL[:resultado.numero_niveis]),
                      delta_color='off', delta_arrow='off')
        return
    diferenca = max(valores.values()) - min(valores.values())
    base = min(valores.values())
    coluna.metric('Diferença entre modelos', f'{formatar_numero(diferenca)} MPa',
                  delta=f'{formatar_percentual(diferenca / base)} do menor E', border=True,
                  delta_color='off', delta_arrow='off')


def _centro(resultado: ResultadoConcreto, destaque: Optional[str]) -> None:
    grafico, tabela = st.columns([2, 1])
    with grafico.container(border=True):
        fig = figura_niveis(resultado, destaque)
        st.pyplot(fig, width='stretch')
        plt.close(fig)
    with tabela.container(border=True):
        st.markdown('**E por nível [MPa]**')
        st.dataframe(colorir_modelos(tabela_por_nivel(resultado)), hide_index=True,
                     width='stretch')
        if resultado.entrada.E_experimental is not None:
            st.caption('Erro = (E do concreto − E experimental) / E experimental.')


def tabela_por_nivel(resultado: ResultadoConcreto) -> pd.DataFrame:
    """Uma linha por modelo, uma coluna por nível (E em MPa) e o erro, se houver E experimental."""
    n = resultado.numero_niveis
    colunas = ['Modelo', *(f'Nível {i}' for i in range(1, n + 1))]
    com_erro = resultado.entrada.E_experimental is not None
    if com_erro:
        colunas.append('Erro')
    linhas = []
    for nome, serie in resultado.series.items():
        valores = [formatar_numero(nv.resultado.Eh) for nv in serie.niveis]
        linha = [nome, *valores, *([SEM_VALOR] * (n - len(valores)))]
        if com_erro:
            erro = serie.erro_relativo
            linha.append(SEM_VALOR if erro is None else formatar_percentual(erro, 2, sinal=True))
        linhas.append(linha)
    return pd.DataFrame(linhas, columns=colunas)


def tabela_propriedades(resultado: ResultadoConcreto) -> pd.DataFrame:
    """Uma linha por modelo e nível com E, ν, K e G (números, para tela e CSV)."""
    linhas = []
    for nome, serie in resultado.series.items():
        for i, nivel in enumerate(serie.niveis, start=1):
            r = nivel.resultado
            linhas.append([nome, i, nivel.nome, float(r.Eh), float(r.vh), float(r.kh),
                           float(r.Gh)])
    return pd.DataFrame(linhas, columns=['Modelo', 'Nível', 'Homogeneizado', 'E [MPa]', 'ν',
                                         'K [MPa]', 'G [MPa]'])


def formatar_propriedades(tabela: pd.DataFrame):
    """Styler com vírgula decimal, módulos sem casas e ν com 3 casas."""
    modulos = ['E [MPa]', 'K [MPa]', 'G [MPa]']
    return (colorir_modelos(tabela)
            .format(formatar_numero, subset=modulos)
            .format(lambda v: formatar_numero(v, 3), subset=['ν']))


def _detalhes(resultado: ResultadoConcreto) -> None:
    st.markdown('#### :material/table_chart: Propriedades por nível')
    tabela = tabela_propriedades(resultado)
    st.dataframe(formatar_propriedades(tabela), hide_index=True, width='stretch')
    st.download_button('Baixar CSV', csv_pt_br(tabela), file_name=nome_csv(resultado),
                       mime='text/csv', icon=':material/download:', key='concreto-csv')
    with st.expander('Frações usadas em cada nível', icon=':material/account_tree:'):
        st.html(html_previa(resultado.entrada))
        st.caption(_nota_poros(resultado))


def _nota_poros(resultado: ResultadoConcreto) -> str:
    e = resultado.entrada
    if e.poros == 0:
        return 'Sem poros: o cálculo para no nível 2.'
    return ('Poros em relação aos sólidos considerados: poros / (sólidos + poros). '
            'Sem ZTI as frações das ZTIs saem da conta.')


def nome_csv(resultado: ResultadoConcreto) -> str:
    return f'hoop-concreto-{resultado.entrada.construcao.replace("_", "-")}-niveis.csv'

