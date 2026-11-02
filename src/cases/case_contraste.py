"""
case_contraste.py — Efeito do contraste de rigidez entre fases.

Compara três sistemas com razões Ei/Em crescentes usando Mori-Tanaka
para mostrar como o contraste influencia a curva Eh/Em vs fi.

Sistemas:
  baixo_contraste : Em = 70 000 MPa,  Ei =  80 000 MPa  →  Ei/Em ≈  1.1×
  concreto        : Em = 30 000 MPa,  Ei =  70 000 MPa  →  Ei/Em ≈  2.3×
  epoxy_vidro     : Em =  3 500 MPa,  Ei =  73 000 MPa  →  Ei/Em ≈ 20.9×
  polimero_aco    : Em =  3 000 MPa,  Ei = 210 000 MPa  →  Ei/Em ≈ 70.0×
  epoxy_carbono   : Em =  3 500 MPa,  Ei = 390 000 MPa  →  Ei/Em ≈111.4×

Modelo : Mori-Tanaka
Estilo : 'normalizar'  →  Y = Eh / Em
Saída  : figuras individuais por sistema + gráfico combinado final

Executar de src/:
    python cases/case_contraste.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import matplotlib.pyplot as plt
import seaborn as sns

from cases._setup import criar_analise, MATERIAIS
from desenho.desenho_mec import DesenhoMecanico
from micmodelos.moritanaka import MoriTanaka

SISTEMAS = [
    ('baixo_contraste', 'Ei/Em ≈ 1.1×',   '#4daf4a'),
    ('concreto',        'Ei/Em ≈ 2.3×',   '#377eb8'),
    ('epoxy_vidro',     'Ei/Em ≈ 20.9×',  '#ff7f00'),
    ('polimero_aco',    'Ei/Em ≈ 70.0×',  '#e41a1c'),
    ('epoxy_carbono',   'Ei/Em ≈ 111.4×', '#984ea3'),
]
MARCADORES = ['o', 's', '^', 'D', '*']

# ── Uma figura individual por sistema ───────────────────────────────────────
instancias = {}
for nome, label, _ in SISTEMAS:
    h = criar_analise(**MATERIAIS[nome])
    d = DesenhoMecanico(estilo='normalizar')
    d.desenha(h, modelo=MoriTanaka())   # figura individual
    instancias[nome] = (h, d, label)

# ── Gráfico combinado — todos os sistemas sobrepostos ───────────────────────
sns.set_style('whitegrid')
fig, ax = plt.subplots(figsize=(10, 5))

for (nome, label, cor), marcador in zip(SISTEMAS, MARCADORES):
    h, d, _ = instancias[nome]
    xs, ys = d.curvas[0].xs, d.curvas[0].ys
    ax.plot(xs, ys,
            label=f'{nome}  ({label})',
            marker=marcador, markersize=4, color=cor)

ax.set_title('Mori-Tanaka — Efeito do Contraste de Rigidez (Ei/Em)')
ax.set_xlabel('fi')
ax.set_ylabel('Eh / Em')
ax.legend(loc='best', fontsize=8)
sns.despine(ax=ax, left=True)
plt.tight_layout()
plt.show()
