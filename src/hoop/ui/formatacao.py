"""Números em pt-BR: formatação para exibição e leitura do texto digitado."""
import math
import re
from typing import Optional


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
    """Lê "30 000", "30e3", "0,3" ou "0.3"; devolve None se não for um número finito."""
    limpo = re.sub(r'[\s  ]', '', str(texto)).replace(',', '.')
    try:
        valor = float(limpo)
    except ValueError:
        return None
    return valor if math.isfinite(valor) else None
