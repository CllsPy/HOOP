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
from f_phases import FPhases

h1 = Homogenizacao()
d = Desenho_Mecanico(estilo='fixar_fracao')

h1.tipo = "global"
h1.analise_tipo = "mecanica"
h1.geo = "esfera"

h1.fi = 0.4
#h1.fr =  0.1
#h1.fm = 0.5

#material 1
h1.Em = 28
h1.vm = 0.2

# material 2
h1.vi = 0.22 #0.3 padrão
h1.Ei = 70

# m3
h1.vii = 0.22
h1.Eii = 50

h1.set_analise()  # cópia dos valores para fazer ANALISE

m1 = Mecanico() # modelo material
m1.E = h1.Em
m1.v = h1.vm
m1.geo = h1.analH.geo

m2 = Mecanico() # modelo material 2
m2.E = h1.Ei
m2.v = h1.vi
m2.geo = h1.analH.geo

#m3 = Mecanico() # modelo material 3
#m3.E = h1.Eii
#m3.v = h1.vii
#m3.geo = h1.analH.geo

h1.calc()
h1.matH.append(m1)
h1.matH.append(m2)
#h1.matH.append(m3)

#h1.calc()
d.desenha(h1, modelo=SelfConsistent())
d.desenha(h1, modelo=MoriTanaka())
d.desenha(h1, modelo=DiluteSuspension())
d.desenha(h1, modelo=Voigt())
d.desenha(h1, modelo=GSC())
#d.desenha(h1, modelo=Counto())
#d.desenha(h1, modelo=Hashin_Inf())
#d.juntar_grafs(h1)
d.bagg()