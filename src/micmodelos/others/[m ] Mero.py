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
from selfconsistent import SelfConsistent
from d_f import DifferentialScheme
from gsc import GSC

h1 = Homogenizacao()
d = Desenhar()

h1.tipo = "global"
h1.analise_tipo = "mecanica"
h1.geo = "esfera"

h1.fi = 0.5
#h1.fm = 0.0000001
#h1.fm = 0.25

#material 1
h1.Em = 200000
h1.vm = 0.25

#material 2
h1.vi = 300000 #0.3 padrão
h1.Ei = 0.45

h1.set_analise()  # cópia dos valores para fazer ANALISE

m1 = Mecanico() # modelo material
m1.E = h1.Em
m1.v = h1.vm
m1.geo = h1.analH.geo


m2 = Mecanico() # modelo material 2
m2.E = h1.Ei
m2.v = h1.vi
m2.geo = h1.analH.geo


h1.matH.append(m1)
h1.matH.append(m2)

# h1.modH = MoriTanaka()
# h1.calc()
# print(h1.modH.Eh)
# h1.modH = SelfConsistent()
# h1.calc()
# print(h1.modH.Eh)
# h1.modH = DiluteSuspension()

h1.calc()

d.desenha(h1, model=DiluteSuspension(), estilo='normalizar')
d.desenha(h1, model=MoriTanaka(), estilo='normalizar')
d.desenha(h1, model=SelfConsistent(), estilo='normalizar')
# d.desenha(h1, model=DifferentialScheme())
d.desenha(h1, model=Reuss(), estilo='normalizar')
d.juntar_grafs(h1, estilo='normalizar')

# #d.desenha(h1, model=GSC(), estilo='poisson')



