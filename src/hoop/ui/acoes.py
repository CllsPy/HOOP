"""Caso de uso "calcular" disparado pelos botões Calcular (Dados) e Recalcular.

Um só fluxo: validar, calcular com progresso por modelo, registrar o resultado
e reexecutar a página (indo para outra etapa, se pedido).
"""
from typing import Optional

import streamlit as st

from hoop.ui.calculo import ResultadoAnalise, calcular, fracoes
from hoop.ui.entrada import EntradaComposito, validar
from hoop.ui.estado import entrada_atual, ir_para, registrar_resultado


def calcular_com_progresso(entrada: EntradaComposito) -> ResultadoAnalise:
    """Calcula mostrando um ``st.status`` com o modelo atual e uma barra de progresso."""
    with st.status('Calculando', expanded=True) as status:
        pontos = f'{len(fracoes(entrada.fi_max))} pontos por modelo'
        barra = st.progress(0.0, text=pontos)

        def ao_progredir(nome: str, concluidos: int, total: int) -> None:
            status.update(label=f'Calculando {nome} · {concluidos} de {total} modelos')
            barra.progress(concluidos / total, text=pontos)

        resultado = calcular(entrada, ao_progredir)
        status.update(label='Cálculo concluído', state='complete')
    return resultado


def calcular_e_registrar(entrada: EntradaComposito, proxima_etapa: Optional[str] = None) -> None:
    """Calcula, guarda o resultado, vai para ``proxima_etapa`` (se dada) e reexecuta."""
    registrar_resultado(calcular_com_progresso(entrada))
    if proxima_etapa:
        ir_para(proxima_etapa)
    st.rerun()


def recalcular() -> None:
    """Recalcula com a entrada atual; erros de entrada viram um ``st.error``."""
    entrada = entrada_atual()
    erros = validar(entrada)
    if erros:
        st.error('Corrija os dados antes de recalcular: ' + ' '.join(erros.values()),
                 icon=':material/error:')
        return
    calcular_e_registrar(entrada)
