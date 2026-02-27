from dataclasses import dataclass, field
from typing import List, Tuple

_MAPA_Y_LABEL = {
    'poisson':      'vh (Coef. de Poisson Homogeneizado)',
    'normalizar':   'Eh / Em (Modulo Normalizado)',
    'fixar_fracao': 'Eh (Modulo de Elasticidade) [MPa]',
}


@dataclass
class DadosEntrada:
    analise_tipo: str
    geo: str
    Em: float
    vm: float
    Ei: float
    vi: float
    fi_max: float
    estilo: str


@dataclass
class DadosModelo:
    nome: str
    xs: List[float]
    ys: List[float]
    y_label: str


@dataclass
class DadosRelatorio:
    entrada: DadosEntrada
    modelos: List[DadosModelo] = field(default_factory=list)


def extrair_dados(objH, d) -> DadosRelatorio:
    """Extrai dados de objH e d em estruturas Python puras."""
    fi_max = max(d.graphs[0][0]) if d.graphs else 0.0
    y_label = _MAPA_Y_LABEL.get(d.estilo, 'y')

    entrada = DadosEntrada(
        analise_tipo=objH.analise_tipo or '',
        geo=objH.analH.geo or '',
        Em=float(objH.Em or 0),
        vm=float(objH.vm or 0),
        Ei=float(objH.Ei or 0),
        vi=float(objH.vi or 0),
        fi_max=fi_max,
        estilo=d.estilo or '',
    )

    modelos = [
        DadosModelo(nome=label, xs=list(xs), ys=list(ys), y_label=y_label)
        for xs, ys, label in d.graphs
    ]

    return DadosRelatorio(entrada=entrada, modelos=modelos)
