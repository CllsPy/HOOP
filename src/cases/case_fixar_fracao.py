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

Executar de src/:
    python cases/case_fixar_fracao.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cases._setup import criar_analise, MATERIAIS
from desenho.desenho_mec import DesenhoMecanico
from relatorio.relatorio import gerar_relatorio

from micmodelos.voigt import Voigt
from micmodelos.reuss import Reuss
from micmodelos.gsc import GSC
from micmodelos.selfconsistent import SelfConsistent
from micmodelos.moritanaka import MoriTanaka
from micmodelos.dilute import DiluteSuspension

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
d.juntar_grafs(h)

# ── Relatório PDF ────────────────────────────────────────────────────────────
gerar_relatorio(h, d, filename='relatorio_fixar_fracao.pdf')
print("Relatório salvo: relatorio_fixar_fracao.pdf")
