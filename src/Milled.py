import matplotlib.pyplot as plt

from hoop.homogenizacao.homogenizacao import Homogenizacao
from hoop.mecanico.mecanico import Mecanico
from hoop.desenho.desenho_mec import DesenhoMecanico
from hoop.relatorio.relatorio import gerar_relatorio

from hoop.micmodelos.dilute import DiluteSuspension
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.selfconsistent import SelfConsistent
from hoop.micmodelos.gsc import GSC

h1 = Homogenizacao()
d = DesenhoMecanico(estilo='fixar_fracao')

h1.tipo = "global"
h1.analise_tipo = "mecanica"
h1.geo = "esfera"

h1.Em = 41000
h1.vm = 0.2

h1.vi = 0.2
h1.Ei = 0.1

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

d.desenha(h1, modelo=GSC())
d.desenha(h1, modelo=SelfConsistent())
d.desenha(h1, modelo=MoriTanaka())
d.desenha(h1, modelo=DiluteSuspension())
d.juntar_grafs()

gerar_relatorio(h1, d, filename='relatorio.pdf')

plt.show()
