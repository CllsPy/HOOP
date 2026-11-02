"""
case_fixar_fracao.py — Módulo de Young homogeneizado (Eh) vs. fração volumétrica.

Sistema: Aço (matriz) + Carboneto de tungstênio — alta rigidez
  Em = 210 000 MPa, vm = 0.30
  Ei = 450 000 MPa, vi = 0.24

Estilo: 'fixar_fracao'  →  Y = Eh [MPa]
Modelos: Voigt (limite sup.), Reuss (limite inf.), GSC, Self-Consistent,
         Mori-Tanaka, Dilute Suspension
Saída  : figuras individuais + gráfico combinado (inclui bandas de Voigt/Reuss)
         + relatorio_fixar_fracao.pdf

Executar da raiz do repositório (com o pacote instalado):
    python src/cases/case_fixar_fracao.py
"""

import matplotlib.pyplot as plt

from hoop.exemplos import criar_analise, MATERIAIS
from hoop.desenho.desenho_mec import DesenhoMecanico
from hoop.relatorio.relatorio import gerar_relatorio

from hoop.micmodelos.voigt import Voigt
from hoop.micmodelos.reuss import Reuss
from hoop.micmodelos.gsc import GSC
from hoop.micmodelos.selfconsistent import SelfConsistent
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.dilute import DiluteSuspension

# ── Configuração ────────────────────────────────────────────────────────────
h = criar_analise(**MATERIAIS['aco_carbeto'])
d = DesenhoMecanico(estilo='fixar_fracao')

# ── Limites (Voigt = superior, Reuss = inferior) ────────────────────────────
d.desenha(h, modelo=Voigt())
d.desenha(h, modelo=Reuss())

# ── Modelos mean-field ───────────────────────────────────────────────────────
d.desenha(h, modelo=GSC())
d.desenha(h, modelo=SelfConsistent())
d.desenha(h, modelo=MoriTanaka())
d.desenha(h, modelo=DiluteSuspension())

# ── Gráfico combinado ────────────────────────────────────────────────────────
d.juntar_grafs()

# ── Relatório PDF ────────────────────────────────────────────────────────────
gerar_relatorio(h, d, filename='relatorio_fixar_fracao.pdf')
print("Relatório salvo: relatorio_fixar_fracao.pdf")

plt.show()
