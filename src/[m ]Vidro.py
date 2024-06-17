# import sys
# from pathlib import Path
# file = Path(__file__).resolve()
# parent, root = file.parent, file.parents[1]
# sys.path.append(str(root))

# BIBLIOTECAS

# CLASSES
from homogenizacao import Homogenizacao
from mecanico import Mecanico
from condutividade import Condutividade
from test import MLHOOP

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
from maxwelleucken import MaxwellEucken
from campbell import Campbell
from hamilton import Hamilton
from popovic import Popovic
from desenho_cond import Desenho_Condutividade

h1 = Homogenizacao()
d = Desenho_Condutividade(estilo='fixar_fracao')

h1.tipo = "global"
h1.analise_tipo = 'condutividade'
h1.geo = 'esfera'
#h1.fi = 0.96

h1.set_analise()

m1 = Condutividade() # modelo material
m1.k11 = 1.38
m1.k22 = 1.38
m1.k33 = 1.38

m2 = Condutividade() # modelo material
m2.k11 = 0.96
m2.k22 = 0.96
m2.k33 = 0.96

h1.matH.append(m1)
h1.matH.append(m2)

d.desenha(h1, modelo=MoriTanaka(), direcao='K22')
d.desenha(h1, modelo=Voigt(), direcao='K22')
d.desenha(h1, modelo=Reuss(), direcao='K22')
d.desenha(h1, modelo=GSC(), direcao='K22')
#d.desenha(h1, modelo=DiluteSuspension(), estilo='fixar_fracao', direcao='K22')
#d.desenha(h1, modelo=SelfConsistent(), estilo='fixar_fracao', direcao='K22')
#d.desenha(h1, modelo=Hashin_Sup(), estilo='fixar_fracao', direcao='K22')
#d.desenha(h1, modelo=Hashin_Inf(), estilo='fixar_fracao', direcao='K22')
d.juntar_grafs(h1, direcao='K22', stats='True')
#url='Mori-Tanaka.csv'
#ml = MLHOOP()
#ml.fazer_previsoes(url, 2)
