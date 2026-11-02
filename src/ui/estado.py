"""Entrada do compósito, presets, validação, formatação pt-BR e ``st.session_state``.

Fluxo das telas:
- Dados lê ``entrada_atual()``, grava com ``definir_entrada(e)``, valida com
  ``validar(e)`` e, ao calcular, chama ``registrar_resultado(calcular(e))``.
- Análise e Relatório leem ``resultado_atual()`` e mostram o aviso de
  recálculo quando ``dados_mudaram()``.
- Análise guarda a grandeza e o fi de leitura com ``definir_leitura``; o
  Relatório e a barra lateral leem ``leitura_atual()``.
- A navegação usa ``ir_para(etapa)`` (serve como ``on_click``).
"""
import re
from dataclasses import dataclass, field, replace
from typing import Dict, Optional, Set, Tuple

import streamlit as st

from ui.calculo import GRANDEZAS, MODELOS, MODELOS_PADRAO, ResultadoAnalise

ETAPAS: Tuple[str, ...] = ('dados', 'analise', 'relatorio')

GEOMETRIAS: Dict[str, str] = {'esfera': 'Esfera', 'cilindro': 'Cilindro', 'disco': 'Disco'}
GEOMETRIAS_DISPONIVEIS: Tuple[str, ...] = ('esfera',)
TIPOS_ANALISE: Dict[str, str] = {'mecanica': 'Mecânica', 'condutividade': 'Condutividade'}
TIPOS_DISPONIVEIS: Tuple[str, ...] = ('mecanica',)

PERSONALIZADO = 'personalizado'
ROTULO_PERSONALIZADO = 'Personalizado'


@dataclass(frozen=True)
class Preset:
    """Material de partida com valores típicos de literatura (E em MPa)."""
    chave: str
    rotulo: str
    Em: float
    vm: float
    Ei: float
    vi: float


PRESETS: Dict[str, Preset] = {
    p.chave: p for p in (
        Preset('concreto', 'Concreto', 30_000, 0.20, 70_000, 0.30),
        Preset('epoxy_vidro', 'Epóxi + fibra de vidro', 3_500, 0.38, 73_000, 0.22),
        Preset('aco_carbeto', 'Aço + carbeto de tungstênio', 210_000, 0.30, 450_000, 0.24),
        Preset('epoxy_carbono', 'Epóxi + fibra de carbono', 3_500, 0.38, 390_000, 0.20),
        Preset('polimero_aco', 'Polímero + esferas de aço', 3_000, 0.35, 210_000, 0.30),
    )
}


@dataclass(frozen=True)
class EntradaComposito:
    """Tudo o que a etapa Dados define. Imutável: use ``dataclasses.replace``.

    ``material`` é a chave de ``PRESETS`` ou ``PERSONALIZADO``; ``modelos`` são
    chaves de ``ui.calculo.MODELOS``.
    """
    Em: float = 30_000.0
    vm: float = 0.20
    Ei: float = 70_000.0
    vi: float = 0.30
    geometria: str = 'esfera'
    tipo_analise: str = 'mecanica'
    modelos: Tuple[str, ...] = field(default=MODELOS_PADRAO)
    fi_max: float = 1.0
    material: str = 'concreto'


@dataclass(frozen=True)
class Leitura:
    """Escolhas da Análise que sobrevivem à troca de etapa: grandeza e fi de leitura."""
    grandeza: str = 'Eh'
    fi: float = 0.30


def aplicar_preset(entrada: EntradaComposito, chave: str) -> EntradaComposito:
    """Copia as propriedades do preset para a entrada, mantendo o resto."""
    p = PRESETS[chave]
    return replace(entrada, Em=p.Em, vm=p.vm, Ei=p.Ei, vi=p.vi, material=chave)


def preset_correspondente(entrada: EntradaComposito) -> str:
    """Chave do preset cujas propriedades batem com a entrada, ou ``PERSONALIZADO``."""
    for p in PRESETS.values():
        if (p.Em, p.vm, p.Ei, p.vi) == (entrada.Em, entrada.vm, entrada.Ei, entrada.vi):
            return p.chave
    return PERSONALIZADO


def rotulo_material(chave: str) -> str:
    return PRESETS[chave].rotulo if chave in PRESETS else ROTULO_PERSONALIZADO


def _erro_modulo(E: float) -> Optional[str]:
    if E > 0:
        return None
    return 'Informe um módulo maior que zero.'


def _erro_poisson(v: float, simbolo: str) -> Optional[str]:
    if v >= 0.5:
        return ('Use um valor menor que 0,5. Com 0,5 o material é incompressível '
                'e os tensores não podem ser invertidos.')
    if v < 0:
        return f'{simbolo} precisa estar entre 0 e 0,5.'
    return None


def validar(entrada: EntradaComposito) -> Dict[str, str]:
    """Erros por campo (nome do atributo -> mensagem); vazio se a entrada é válida."""
    erros = {
        'Em': _erro_modulo(entrada.Em),
        'Ei': _erro_modulo(entrada.Ei),
        'vm': _erro_poisson(entrada.vm, 'νm'),
        'vi': _erro_poisson(entrada.vi, 'νi'),
    }
    if not entrada.modelos:
        erros['modelos'] = 'Selecione ao menos um modelo para comparar.'
    elif any(m not in MODELOS for m in entrada.modelos):
        erros['modelos'] = 'Há um modelo desconhecido na seleção.'
    if not 0 < entrada.fi_max <= 1:
        erros['fi_max'] = 'Escolha um fi máximo maior que 0 e até 1.'
    if entrada.geometria not in GEOMETRIAS_DISPONIVEIS:
        erros['geometria'] = 'Esta geometria ainda está em validação. Use esfera.'
    if entrada.tipo_analise not in TIPOS_DISPONIVEIS:
        erros['tipo_analise'] = 'A análise de condutividade chega em breve. Use mecânica.'
    return {campo: msg for campo, msg in erros.items() if msg}


def resumo_entrada(entrada: EntradaComposito) -> str:
    """Resumo curto para a barra lateral: "Concreto · esfera · 5 modelos"."""
    n = len(entrada.modelos)
    modelos = f'{n} modelo' if n == 1 else f'{n} modelos'
    geometria = GEOMETRIAS.get(entrada.geometria, entrada.geometria).lower()
    return f'{rotulo_material(entrada.material)} · {geometria} · {modelos}'


def resumo_leitura(leitura: Leitura) -> str:
    """Resumo da Análise para a barra lateral: "Eh · leitura em fi 0,30"."""
    return f'{GRANDEZAS[leitura.grandeza].simbolo} · leitura em fi {formatar_decimal(leitura.fi)}'


def formatar_numero(valor: float, casas: int = 0) -> str:
    """Número pt-BR: espaço como separador de milhar e vírgula decimal (30000 -> "30 000")."""
    texto = f'{valor:,.{casas}f}'
    return texto.replace(',', ' ').replace('.', ',').replace('-', '−')


def formatar_decimal(valor: float, casas: int = 2) -> str:
    """Decimal pt-BR com casas fixas (0.3 -> "0,30")."""
    return formatar_numero(valor, casas)


def formatar_percentual(fracao: float, casas: int = 1, sinal: bool = False) -> str:
    """Fração como percentual (0.274 -> "27,4%"; com ``sinal``, "+27,4%")."""
    texto = formatar_numero(fracao * 100, casas) + '%'
    return '+' + texto if sinal and fracao > 0 else texto


def interpretar_numero(texto: str) -> Optional[float]:
    """Lê "30 000", "30e3", "0,3" ou "0.3"; devolve None se não for um número."""
    limpo = re.sub(r'[\s  ]', '', str(texto)).replace(',', '.')
    try:
        return float(limpo)
    except ValueError:
        return None


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
