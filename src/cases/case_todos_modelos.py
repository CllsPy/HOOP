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

Executar de src/:
    python cases/case_todos_modelos.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cases._setup import criar_analise, MATERIAIS
from desenho.desenho_mec import DesenhoMecanico
from relatorio.relatorio import gerar_relatorio

from micmodelos.voigt import Voigt
from micmodelos.reuss import Reuss
from micmodelos.popovic import Popovic
from micmodelos.dilute import DiluteSuspension
from micmodelos.moritanaka import MoriTanaka
from micmodelos.selfconsistent import SelfConsistent
from micmodelos.gsc import GSC

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
d.juntar_grafs(h)

# ── Relatório PDF ────────────────────────────────────────────────────────────
gerar_relatorio(h, d, filename='relatorio_todos_modelos.pdf')
print("Relatório salvo: relatorio_todos_modelos.pdf")
