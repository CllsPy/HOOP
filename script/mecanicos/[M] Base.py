
from homogenizacao import Homogenizacao
from mecanico import Mecanico
from desenho_mec import Desenho_Mecanico
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

# Criar instâncias
h1 = Homogenizacao() # Classe mãe
d = Desenho_Mecanico(estilo='fixar_fracao') # Classe desenho mecânico

# Definir problema
h1.tipo = "global" # Tipo
h1.analise_tipo = "mecanica" # Tipo de análise
h1.geo = "esfera" # Geometria

# Definir fração
h1.fi = 0.4

# Primeiro material
h1.Em = 28
h1.vm = 0.2

# Segundo Material
h1.vi = 0.22
h1.Ei = 70

# Criar cópia do problema
h1.set_analise()

# Definir propriedades dos materiais
m1 = Mecanico() # Material 1
m1.E = h1.Em
m1.v = h1.vm
m1.geo = h1.analH.geo

m2 = Mecanico() # Material 2
m2.E = h1.Ei
m2.v = h1.vi
m2.geo = h1.analH.geo

# Adicionar materiais a lista
h1.matH.append(m1)
h1.matH.append(m2)

# Desenhar problema
d.desenha(h1, modelo=SelfConsistent())
d.desenha(h1, modelo=MoriTanaka())
d.desenha(h1, modelo=DiluteSuspension())
d.desenha(h1, modelo=Voigt())
d.desenha(h1, modelo=GSC())

# Agregar os gráficos
d.juntar_grafs(h1)
