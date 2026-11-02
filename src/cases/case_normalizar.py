"""
case_normalizar.py — Módulo normalizado (Eh/Em) vs. fração volumétrica.

Sistema: Concreto (matriz) + Agregado graúdo (inclusão)
  Em = 30 000 MPa, vm = 0.20
  Ei = 70 000 MPa, vi = 0.30

Estilo: 'normalizar'  →  Y = Eh / Em  (módulo adimensional)
Modelos: GSC, Self-Consistent, Mori-Tanaka, Dilute Suspension
Saída  : figuras individuais + gráfico combinado + relatorio_normalizar.pdf

Executar da raiz do repositório (com o pacote instalado):
    python src/cases/case_normalizar.py
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
h = criar_analise(**MATERIAIS['concreto'])
d = DesenhoMecanico(estilo='normalizar')

# ── Plotagem individual de cada modelo ──────────────────────────────────────
d.desenha(h, modelo=GSC())
d.desenha(h, modelo=SelfConsistent())
d.desenha(h, modelo=MoriTanaka())
d.desenha(h, modelo=DiluteSuspension())

# ── Gráfico combinado ────────────────────────────────────────────────────────
d.juntar_grafs()

# ── Relatório PDF ────────────────────────────────────────────────────────────
gerar_relatorio(h, d, filename='relatorio_normalizar.pdf')
print("Relatório salvo: relatorio_normalizar.pdf")

plt.show()
