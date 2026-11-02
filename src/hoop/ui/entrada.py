"""Entrada do compósito: presets, catálogo de geometrias e tipos, validação e resumo."""
import math
from dataclasses import dataclass, field, replace
from typing import Dict, Optional, Tuple

from hoop.ui.calculo import MODELOS, MODELOS_PADRAO

GEOMETRIAS: Dict[str, str] = {'esfera': 'Esfera', 'cilindro': 'Cilindro', 'disco': 'Disco'}
GEOMETRIAS_DISPONIVEIS: Tuple[str, ...] = ('esfera',)
INCLUSOES: Dict[str, str] = {'esfera': 'inclusões esféricas', 'cilindro': 'inclusões cilíndricas',
                             'disco': 'inclusões em disco'}
"""Geometria no plural, para títulos e subtítulos: "Concreto com inclusões esféricas"."""
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
    chaves de ``hoop.ui.calculo.MODELOS``.
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
    if math.isfinite(E) and E > 0:
        return None
    return 'Informe um módulo maior que zero.'


def _erro_poisson(v: float, simbolo: str) -> Optional[str]:
    if not math.isfinite(v):
        return f'{simbolo} precisa estar entre 0 e 0,5.'
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
