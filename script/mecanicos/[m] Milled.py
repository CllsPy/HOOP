# import sys
# from pathlib import Path
# file = Path(__file__).resolve()
# parent, root = file.parent, file.parents[1]
# sys.path.append(str(root))

# BIBLIOTECAS

# CLASSES
from homogenizacao import Homogenizacao
from mecanico import Mecanico
from desenho_mec import Desenho_Mecanico

# MODELOS
from voigt import Voigt
from hashin_inf import Hashin_Inf
from hashin_sup import Hashin_Sup
from reuss import Reuss
from dilute import DiluteSuspension
from couto import Counto
from moritanaka import MoriTanaka
from selfconsistent import SelfConsistent
from gsc import GSC
from d_f import DifferentialScheme

h1 = Homogenizacao()
d = Desenho_Mecanico(estilo='normalizar')

h1.tipo = "global"
h1.analise_tipo = "mecanica"
h1.geo = "esfera"

#h1.fi = 0.7
#h1.fm = 0.0000001
#h1.fm = 0.75

#material 1
h1.Em = 41000
h1.vm = 0.2

#material 2
h1.vi = 0.2 #0.3 padrão
h1.Ei = 0.1

h1.set_analise()  # cópia dos valores para fazer ANALISE

m1 = Mecanico() # modelo material
m1.E = h1.Em
m1.v = h1.vm
m1.geo = h1.analH.geo


m2 = Mecanico() # modelo material 2
m2.E = h1.Ei
m2.v = h1.vi
m2.geo = h1.analH.geo

# fi, fm = h1.analH.corrigeFrac(h1.analH.fi, h1.analH.fm) # corrigir frações com as cópias dos valores
# h1.analH.fi = fi
# h1.analH.fm = fm

h1.matH.append(m1)
h1.matH.append(m2)

h1.calc()

d.desenha(h1, modelo=GSC())
d.desenha(h1, modelo=SelfConsistent())
d.desenha(h1, modelo=MoriTanaka())
d.desenha(h1, modelo=DiluteSuspension())
d.juntar_grafs(h1)

#lista = [Reuss(), Voigt(), MoriTanaka(), GSC()]
#d.hist(h1, lista)


