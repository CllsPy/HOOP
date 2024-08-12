
from homogenizacao import Homogenizacao
from mecanico import Mecanico
from desenho_mec import DesenhoMecanico
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

d = DesenhoMecanico(estilo='fixar_fracao')
h1 = Homogenizacao()

h1.tipo = "global"
h1.analise_tipo = "mecanica"
h1.geo = "esfera"

h1.fi = 0.4
h1.Em = 28
h1.vm = 0.2

h1.vi = 0.22
h1.Ei = 70

h1.set_analise()

m1 = Mecanico()
m1.E = h1.Em
m1.v = h1.vm
m1.geo = h1.analH.geo

m2 = Mecanico()
m2.E = h1.Ei
m2.v = h1.vi
m2.geo = h1.analH.geo

m3 = Mecanico()
m3.E = h1.Ei
m3.v = h1.vi
m3.geo = h1.analH.geo

h1.matH.append(m1)
h1.matH.append(m2)
# h1.matH.append(m3)

d.desenha(h1, modelo=SelfConsistent())
d.desenha(h1, modelo=MoriTanaka())
d.desenha(h1, modelo=DiluteSuspension())
d.desenha(h1, modelo=Voigt())
d.desenha(h1, modelo=GSC())

d.juntar_grafs(h1)
