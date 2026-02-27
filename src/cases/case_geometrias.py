"""
case_geometrias.py — Efeito da geometria da inclusão no módulo homogeneizado.

Compara o mesmo modelo micromecânico (Mori-Tanaka) aplicado a três
geometrias de inclusão distintas:
  - Esfera  (aspect ratio = 1)
  - Cilindro (fibra longa)
  - Disco   (plaqueta achatada)

Sistema: Epóxi (matriz) + Fibra de vidro (inclusão)
  Em =  3 500 MPa, vm = 0.38
  Ei = 73 000 MPa, vi = 0.22

Estilo: 'normalizar'  →  Y = Eh / Em
Saída  : 3 figuras individuais (uma por geometria) + gráfico manual combinado

NOTA: cilindro e disco usam tensor de Eshelby analítico — resultados
      aproximados; validar contra literatura antes de usar em produção.

Executar de src/:
    python cases/case_geometrias.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import matplotlib.pyplot as plt
import seaborn as sns

from cases._setup import criar_analise, MATERIAIS
from desenho.desenho_mec import DesenhoMecanico
from micmodelos.moritanaka import MoriTanaka

MAT = MATERIAIS['epoxy_vidro']
GEOMETRIAS = ['esfera', 'cilindro', 'disco']
MARCADORES = ['o', 's', '^']
CORES = ['#1f77b4', '#ff7f0e', '#2ca02c']

# ── Uma DesenhoMecanico + Homogenizacao por geometria ───────────────────────
instancias = {}
for geo in GEOMETRIAS:
    h = criar_analise(**MAT, geo=geo)
    d = DesenhoMecanico(estilo='normalizar')
    d.desenha(h, modelo=MoriTanaka())
    d.juntar_grafs(h)          # figura individual por geometria
    instancias[geo] = (h, d)

# ── Gráfico manual comparando as 3 geometrias ───────────────────────────────
sns.set_style('whitegrid')
fig, ax = plt.subplots(figsize=(10, 5))

for (geo, (h, d)), marcador, cor in zip(instancias.items(), MARCADORES, CORES):
    xs, ys, _ = d.graphs[0]
    ax.plot(xs, ys, label=f'Mori-Tanaka ({geo})',
            marker=marcador, markersize=4, color=cor)

ax.set_title('Mori-Tanaka — Efeito da Geometria da Inclusão')
ax.set_xlabel('fi')
ax.set_ylabel('Eh / Em')
ax.legend(loc='best')
sns.despine(ax=ax, left=True)
plt.tight_layout()
plt.show()
