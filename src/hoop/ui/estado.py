"""Estado da interface em ``st.session_state``: etapa, entrada, resultado e leitura.

Fluxo das telas:
- Dados lê ``entrada_atual()``, grava com ``definir_entrada(e)`` e, ao
  calcular, chama ``registrar_resultado(calcular(e))``.
- Análise e Relatório leem ``resultado_atual()`` e mostram o aviso de
  recálculo quando ``dados_mudaram()``.
- Análise guarda a grandeza e o fi de leitura com ``definir_leitura``; o
  Relatório e a barra lateral leem ``leitura_atual()``.
- A navegação usa ``ir_para(etapa)`` (serve como ``on_click``).
"""
from dataclasses import dataclass
from typing import Optional, Set, Tuple

import streamlit as st

from hoop.ui.calculo import GRANDEZAS, ResultadoAnalise
from hoop.ui.entrada import EntradaComposito
from hoop.ui.formatacao import formatar_decimal

ETAPAS: Tuple[str, ...] = ('dados', 'analise', 'relatorio')


@dataclass(frozen=True)
class Leitura:
    """Escolhas da Análise que sobrevivem à troca de etapa: grandeza e fi de leitura."""
    grandeza: str = 'Eh'
    fi: float = 0.30


def resumo_leitura(leitura: Leitura) -> str:
    """Resumo da Análise para a barra lateral: "Eh · leitura em fi 0,30"."""
    return f'{GRANDEZAS[leitura.grandeza].simbolo} · leitura em fi {formatar_decimal(leitura.fi)}'


_CHAVE_ETAPA = 'hoop_etapa'
_CHAVE_ENTRADA = 'hoop_entrada'
_CHAVE_RESULTADO = 'hoop_resultado'
_CHAVE_LEITURA = 'hoop_leitura'


def etapa_atual() -> str:
    """Etapa exibida (uma de ``ETAPAS``); cai para 'dados' se a etapa não está liberada."""
    etapa = st.session_state.get(_CHAVE_ETAPA, 'dados')
    return etapa if etapa in etapas_liberadas() else 'dados'


def ir_para(etapa: str) -> None:
    """Troca a etapa exibida. Use como ``on_click=ir_para, args=('analise',)``."""
    if etapa not in ETAPAS:
        raise ValueError(f"Etapa desconhecida: '{etapa}'. Use uma de {ETAPAS}.")
    st.session_state[_CHAVE_ETAPA] = etapa


def entrada_atual() -> EntradaComposito:
    """Entrada em edição; o padrão é o concreto com os 5 modelos."""
    return st.session_state.get(_CHAVE_ENTRADA, EntradaComposito())


def definir_entrada(entrada: EntradaComposito) -> None:
    st.session_state[_CHAVE_ENTRADA] = entrada


def resultado_atual() -> Optional[ResultadoAnalise]:
    """Último resultado calculado, ou None antes do primeiro cálculo."""
    return st.session_state.get(_CHAVE_RESULTADO)


def registrar_resultado(resultado: ResultadoAnalise) -> None:
    """Guarda o resultado; ``resultado.entrada`` vira a referência de ``dados_mudaram``."""
    st.session_state[_CHAVE_RESULTADO] = resultado


def dados_mudaram() -> bool:
    """True se há resultado e a entrada atual difere da usada no cálculo."""
    resultado = resultado_atual()
    return resultado is not None and resultado.entrada != entrada_atual()


def etapas_liberadas() -> Set[str]:
    """Dados sempre; Análise e Relatório depois do primeiro cálculo."""
    return set(ETAPAS) if resultado_atual() is not None else {'dados'}


def leitura_atual() -> Leitura:
    """Grandeza e fi escolhidos na Análise; o padrão é Eh em fi 0,30."""
    return st.session_state.get(_CHAVE_LEITURA, Leitura())


def definir_leitura(leitura: Leitura) -> None:
    st.session_state[_CHAVE_LEITURA] = leitura
