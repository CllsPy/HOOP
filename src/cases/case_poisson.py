"""
case_poisson.py — Coeficiente de Poisson homogeneizado vs. fração volumétrica.

Sistema: Epóxi (matriz) + Fibra de vidro (inclusão)
  Em = 3 500 MPa,  vm = 0.38
  Ei = 73 000 MPa, vi = 0.22

Estilo: 'poisson'  →  Y = vh (coef. Poisson homogeneizado)
Modelos: GSC, Self-Consistent, Mori-Tanaka, Dilute Suspension
Saída  : figuras individuais + gráfico combinado + relatorio_poisson.pdf

Executar da raiz do repositório (com o pacote instalado):
    python src/cases/case_poisson.py
"""

import matplotlib.pyplot as plt

from hoop.exemplos import criar_analise, MATERIAIS
from hoop.desenho.desenho_mec import DesenhoMecanico
from hoop.relatorio.relatorio import gerar_relatorio

from hoop.micmodelos.gsc import GSC
from hoop.micmodelos.selfconsistent import SelfConsistent
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.dilute import DiluteSuspension

# ── Configuração ────────────────────────────────────────────────────────────
h = criar_analise(**MATERIAIS['epoxy_vidro'])
d = DesenhoMecanico(estilo='poisson')

# ── Plotagem individual de cada modelo ──────────────────────────────────────
d.desenha(h, modelo=GSC())
d.desenha(h, modelo=SelfConsistent())
d.desenha(h, modelo=MoriTanaka())
d.desenha(h, modelo=DiluteSuspension())

# ── Gráfico combinado ────────────────────────────────────────────────────────
d.juntar_grafs()

# ── Relatório PDF ────────────────────────────────────────────────────────────
gerar_relatorio(h, d, filename='relatorio_poisson.pdf')
print("Relatório salvo: relatorio_poisson.pdf")

plt.show()
