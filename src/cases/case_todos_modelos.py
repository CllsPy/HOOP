"""
case_todos_modelos.py — Comparação de TODOS os 7 modelos disponíveis.

Sistema: Polímero (matriz) + Esferas de aço (inclusão) — alto contraste
  Em =   3 000 MPa, vm = 0.35
  Ei = 210 000 MPa, vi = 0.30
  Razão Ei/Em ≈ 70×

Estilo: 'normalizar'  →  Y = Eh / Em
Modelos:
  Limites  : Voigt, Reuss
  Média     : Popovic (média de Voigt e Reuss)
  Mean-field: Dilute Suspension, Mori-Tanaka, Self-Consistent, GSC
Saída  : figuras individuais + gráfico combinado com todos os 7 modelos
         + relatorio_todos_modelos.pdf

Executar da raiz do repositório (com o pacote instalado):
    python src/cases/case_todos_modelos.py
"""

import matplotlib.pyplot as plt

from hoop.exemplos import criar_analise, MATERIAIS
from hoop.desenho.desenho_mec import DesenhoMecanico
from hoop.relatorio.relatorio import gerar_relatorio

from hoop.micmodelos.voigt import Voigt
from hoop.micmodelos.reuss import Reuss
from hoop.micmodelos.popovic import Popovic
from hoop.micmodelos.dilute import DiluteSuspension
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.selfconsistent import SelfConsistent
from hoop.micmodelos.gsc import GSC

# ── Configuração ────────────────────────────────────────────────────────────
h = criar_analise(**MATERIAIS['polimero_aco'])
d = DesenhoMecanico(estilo='normalizar')

# ── Limites de Voigt-Reuss ───────────────────────────────────────────────────
d.desenha(h, modelo=Voigt())          # limite superior
d.desenha(h, modelo=Reuss())          # limite inferior
d.desenha(h, modelo=Popovic())        # média aritmética Voigt + Reuss

# ── Modelos mean-field ───────────────────────────────────────────────────────
d.desenha(h, modelo=DiluteSuspension())   # válido para fi << 1
d.desenha(h, modelo=MoriTanaka())         # interação entre inclusões
d.desenha(h, modelo=SelfConsistent())     # iterativo — ampla faixa
d.desenha(h, modelo=GSC())               # composite sphere assemblage

# ── Gráfico combinado com todos os 7 modelos ────────────────────────────────
d.juntar_grafs()

# ── Relatório PDF ────────────────────────────────────────────────────────────
gerar_relatorio(h, d, filename='relatorio_todos_modelos.pdf')
print("Relatório salvo: relatorio_todos_modelos.pdf")

plt.show()
