from dataclasses import dataclass
from typing import Optional


@dataclass
class Analise:
    """Parâmetros de uma análise de homogeneização."""
    analise_type: str        # 'mecanica' ou 'condutividade'
    geo: str                 # geometria da inclusão: 'esfera', 'cilindro', 'disco'
    fi: float                # fração volumétrica da inclusão
    fm: float                # fração volumétrica da matriz
    fr: Optional[float]      # fração volumétrica da terceira fase (quando houver)
