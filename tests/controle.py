# import sys
# from pathlib import Path
# file = Path(__file__).resolve()
# parent, root = file.parent, file.parents[1]
# sys.path.append(str(root))

# BIBLIOTECAS

# CLASSES
from homogenizacao import Homogenizacao
from mecanico import Mecanico
from desenho_mec import Desenhar

# MODELOS
from voigt import Voigt
from hashin_inf import Hashin_Inf
from hashin_sup import Hashin_Sup
from reuss import Reuss
from dilute import DiluteSuspension
from couto import Counto
from moritanaka import MoriTanaka

h1 = Homogenizacao()
d = Desenhar()

h1.tipo = "global"
h1.analise_tipo = "mecanica"
h1.geo = "esfera"
h1.fi = 0.2690
h1.fm = 0.1540

h1.set_analise()  # cópia dos valores para fazer ANALISE

E1 = 36.76*10**9
v1 = 0.35

m1 = Mecanico() # modelo material 1
m1.E = E1
m1.v = v1
m1.geo = h1.analH.geo

E2 = 77.60*10**9
v2 = 0.15

m2 = Mecanico() # modelo material 2
m2.E = E2
m2.v = v2
m2.geo = h1.analH.geo

fi, fm = h1.analH.corrigeFrac(h1.analH.fi, h1.analH.fm) # corrigir frações com as cópias dos valores
h1.analH.fi = fi
h1.analH.fm = fm

h1.matH.append(m1)
h1.matH.append(m2)

h1.calc()  # Porque precisa disso aqui??

d.desenha(h1, Hashin_Sup())
d.desenha(h1, Hashin_Inf())
d.desenha(h1, DiluteSuspension())
d.desenha(h1, MoriTanaka())

#d.desenha(h1, Voigt())
#d.desenha(h1, Reuss())
#d.desenha(h1, DiluteSuspension())
#d.desenha(h1, Counto())
#d.desenha(h1, MoriTanaka())
# d.desenha(h1, DiluteSuspension())
d.juntar_grafs()
