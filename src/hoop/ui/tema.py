"""Tokens do design system do HOOP (tema claro) e sua aplicação no app.

- ``CORES``: tokens de cor do ``tokens.json`` (chave = nome do token).
- ``SERIES`` / ``MARCADORES`` / ``TRACEJADOS``: cor, marcador e estilo de linha
  de cada modelo, pela chave de ``hoop.ui.calculo.MODELOS``.
- ``GLIFOS``: SVGs inline (marca e geometrias) com ``currentColor``.
- ``aplicar_tema()``: injeta o CSS mínimo; chamar uma vez por execução.
- ``estilo_matplotlib()``: contexto ``rc`` do DS para as figuras.
"""
from contextlib import contextmanager
from functools import lru_cache
from typing import Dict, Iterator, List

import matplotlib as mpl
import streamlit as st
from matplotlib import font_manager

CORES: Dict[str, str] = {
    'surface-0': '#F6F7F5',
    'surface-1': '#FFFFFF',
    'surface-2': '#ECEFEC',
    'line': '#D5DBD8',
    'line-strong': '#8F9C99',
    'ink': '#142120',
    'ink-muted': '#4F5E5C',
    'accent': '#0B6E6E',
    'accent-strong': '#08585A',
    'accent-soft': '#DDEFEE',
    'on-accent': '#FFFFFF',
    'phase-matrix': '#3E6F8A',
    'phase-inclusion': '#A85A0C',
    'success': '#2E7D4F',
    'warning': '#9A5800',
    'danger': '#B3261E',
    'warning-soft': '#FBF0DE',
    'danger-soft': '#FBE5E3',
    'series-bounds': '#6E7C7A',
    'band-bounds': '#E4E9E7',
    'series-mt': '#0B6E6E',
    'series-sc': '#C2620F',
    'series-gsc': '#2F55C8',
    'series-dilute': '#8E3B8A',
    'series-popovic': '#5F7316',
}

SERIES: Dict[str, str] = {
    'Voigt': CORES['series-bounds'],
    'Reuss': CORES['series-bounds'],
    'Dilute Suspension': CORES['series-dilute'],
    'Mori-Tanaka': CORES['series-mt'],
    'Self-Consistent': CORES['series-sc'],
    'GSC': CORES['series-gsc'],
    'Popovic': CORES['series-popovic'],
}

MARCADORES: Dict[str, str] = {
    'Voigt': '',
    'Reuss': '',
    'Mori-Tanaka': 'o',
    'Self-Consistent': 's',
    'GSC': '^',
    'Dilute Suspension': 'D',
    'Popovic': 'x',
}

TRACEJADOS: Dict[str, str] = {'Voigt': '--', 'Reuss': '--'}
"""Estilo de linha diferente de contínuo; os demais modelos usam '-'."""

CORES_FASE: Dict[str, str] = {
    'matriz': CORES['phase-matrix'],
    'inclusao': CORES['phase-inclusion'],
}

FONTES = {
    'display': 'Archivo',
    'sans': 'Source Sans 3',
    'mono': 'IBM Plex Mono',
}
URL_FONTES = (
    'https://fonts.googleapis.com/css2?family=Archivo:wght@600;700'
    '&family=IBM+Plex+Mono:wght@500&family=Source+Sans+3:wght@400;600&display=swap'
)

GLIFOS: Dict[str, str] = {
    'esfera': (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
        'stroke-linecap="round"><circle cx="12" cy="12" r="8"/>'
        '<path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>'
        '<path d="M4 12c0-1.7 3.6-3 8-3s8 1.3 8 3" stroke-dasharray="1.5 2.5"/></svg>'
    ),
    'cilindro': (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
        'stroke-linecap="round"><ellipse cx="12" cy="5" rx="4" ry="1.75"/>'
        '<path d="M8 5v14c0 1 1.8 1.75 4 1.75s4-.75 4-1.75V5"/></svg>'
    ),
    'disco': (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
        'stroke-linecap="round"><ellipse cx="12" cy="10.5" rx="8.5" ry="3.25"/>'
        '<path d="M3.5 10.5v2.5c0 1.8 3.8 3.25 8.5 3.25s8.5-1.45 8.5-3.25v-2.5"/></svg>'
    ),
    'marca': (
        '<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" '
        'stroke="currentColor" stroke-width="1.75"/>'
        f'<circle cx="9.2" cy="9.6" r="1.7" fill="{CORES["phase-inclusion"]}"/>'
        f'<circle cx="14.8" cy="10.4" r="1.3" fill="{CORES["phase-inclusion"]}"/>'
        f'<circle cx="11.6" cy="15" r="1.5" fill="{CORES["phase-inclusion"]}"/></svg>'
    ),
}

_CSS = f"""
<style>
[data-testid="stMetricValue"], .hoop-dado {{
  font-family: '{FONTES['mono']}', ui-monospace, monospace;
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}}
[data-testid="stMetricLabel"] p {{ font-weight: 600; color: {CORES['ink-muted']}; }}
.hoop-sobretitulo {{
  font-size: 13px; font-weight: 600; letter-spacing: .06em;
  text-transform: uppercase; color: {CORES['ink-muted']};
}}
.hoop-mudo {{ color: {CORES['ink-muted']}; }}
.hoop-marca {{ display: flex; gap: 10px; align-items: center; color: {CORES['ink']}; }}
.hoop-marca svg {{ width: 32px; height: 32px; flex: none; }}
.hoop-marca b {{
  font-family: '{FONTES['display']}', sans-serif; font-size: 20px;
  letter-spacing: .04em; display: block; line-height: 24px;
}}
.hoop-marca small {{ font-size: 13px; color: {CORES['ink-muted']}; }}
.hoop-glifo svg {{ width: 20px; height: 20px; vertical-align: -4px; }}
.hoop-fase {{ font-weight: 600; }}
.hoop-fase-matriz {{ color: {CORES['phase-matrix']}; }}
.hoop-fase-inclusao {{ color: {CORES['phase-inclusion']}; }}
.hoop-quadrado {{
  display: inline-block; width: 12px; height: 12px; border-radius: 2px;
  margin-right: 8px; vertical-align: 0;
}}
.hoop-amostra {{
  display: inline-block; width: 18px; height: 0; margin-right: 8px;
  border-top: 3px solid; vertical-align: 4px;
}}
.hoop-amostra-tracejada {{ border-top-style: dashed; border-top-width: 2px; }}
[class*="st-key-passo-"] {{ border-radius: 6px; padding: 2px 4px 6px; gap: 0; }}
[class*="st-key-passo-atual"] {{ background: {CORES['accent-soft']}; }}
[class*="st-key-passo-"] button {{ justify-content: flex-start; font-weight: 600; }}
[class*="st-key-passo-"] button p {{ font-weight: 600; }}
[class*="st-key-passo-concluida"] [data-testid="stIconMaterial"] {{ color: {CORES['success']}; }}
[class*="st-key-passo-atual"] [data-testid="stIconMaterial"] {{ color: {CORES['accent']}; }}
[class*="st-key-passo-"] [data-testid="stCaptionContainer"] {{ padding-left: 28px; }}
</style>
"""


def aplicar_tema() -> None:
    """Injeta o CSS do DS na página atual (as fontes vêm de .streamlit/config.toml)."""
    st.html(_CSS)


@lru_cache(maxsize=None)
def _familias_instaladas(*preferidas: str) -> List[str]:
    """Filtra as famílias que o matplotlib encontra, mantendo DejaVu Sans como reserva."""
    instaladas = {f.name for f in font_manager.fontManager.ttflist}
    return [f for f in preferidas if f in instaladas] + ['DejaVu Sans']


def rc_matplotlib() -> Dict[str, object]:
    """Parâmetros ``rcParams`` do DS para gráficos sobre ``surface-1``."""
    return {
        'figure.facecolor': CORES['surface-1'],
        'axes.facecolor': CORES['surface-1'],
        'savefig.facecolor': CORES['surface-1'],
        'axes.edgecolor': CORES['line'],
        'axes.labelcolor': CORES['ink-muted'],
        'axes.grid': True,
        'axes.axisbelow': True,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'grid.color': CORES['band-bounds'],
        'grid.linewidth': 0.8,
        'xtick.color': CORES['ink-muted'],
        'ytick.color': CORES['ink-muted'],
        'xtick.labelcolor': CORES['ink-muted'],
        'ytick.labelcolor': CORES['ink-muted'],
        'text.color': CORES['ink'],
        'legend.frameon': False,
        'font.family': 'sans-serif',
        'font.sans-serif': _familias_instaladas(FONTES['sans']),
        'font.size': 10,
        'axes.labelsize': 10,
    }


@contextmanager
def estilo_matplotlib() -> Iterator[None]:
    """Contexto ``with estilo_matplotlib():`` para criar figuras no estilo do DS."""
    with mpl.rc_context(rc_matplotlib()):
        yield
