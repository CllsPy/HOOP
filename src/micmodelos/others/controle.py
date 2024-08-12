from homogenizacao.homogenizacao import Homogenizacao
from mecanico.mecanico import Mecanico
from desenho.desenho_mec import DesenhoMecanico
from micmodelos.voigt import Voigt

h1 = Homogenizacao()
d = DesenhoMecanico(estilo="fixar_fracao")

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

d.desenha(h1, Voigt())
