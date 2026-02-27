from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class ResultadoMecanico:
    """Contrato formal de saída para análise mecânica.
    Qualquer modelo micromecânico deve ser capaz de produzir este objeto.
    """
    Eh: float = 0.0    # Módulo de elasticidade homogeneizado
    vh: float = 0.0    # Coeficiente de Poisson homogeneizado
    kh: float = 0.0    # Módulo volumétrico homogeneizado
    Gh: float = 0.0    # Módulo cisalhante homogeneizado
    Em: float = 0.0    # Módulo da matriz (referência para normalização)
    fi: float = 0.0    # Fração volumétrica de inclusão usada
    C:  Optional[np.ndarray] = field(default=None)   # Tensor constitutivo 6x6


@dataclass
class ResultadoCondutividade:
    """Contrato formal de saída para análise de condutividade térmica."""
    K11: float = 0.0
    K22: float = 0.0
    K33: float = 0.0
    fi:  float = 0.0
    kh:  Optional[np.ndarray] = field(default=None)  # Tensor 3x3
