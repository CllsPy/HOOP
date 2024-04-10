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
from d_f import DifferentialScheme
from gsc import GSC
# from desenho_mec import Desenho_Mec

h1 = Homogenizacao()
d = Desenho_Mecanico(estilo='fixar_fracao')

h1.tipo = "global"
h1.analise_tipo = "mecanica"
h1.geo = "esfera"

h1.Em = 1.32
h1.vm = 0.3

h1.vi = 0.2
h1.Ei = 40.50

h1.set_analise()
m1 = Mecanico()

m1.E = h1.Em
m1.v = h1.vm
m1.geo = h1.analH.geo

m2 = Mecanico()
m2.E = h1.Ei
m2.v = h1.vi
m2.geo = h1.analH.geo

h1.matH.append(m1)
h1.matH.append(m2)

h1.calc()
d.desenha(h1, Reuss())
d.desenha(h1, Voigt())
d.desenha(h1, MoriTanaka())
d.juntar_grafs(h1, stats='True')
#modelos = [Reuss(), Voigt(), MoriTanaka(), SelfConsistent(), GSC()]
#d.hist(h1, modelos)