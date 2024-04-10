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


'''
1. Defina o problema
'''
h1 = Homogenizacao()
d = Desenho_Condutividade(estilo='fixar_fracao')

h1.tipo = "global"
h1.analise_tipo = 'condutividade'
h1.geo = 'esfera'

h1.fi = 0.4
h1.fr =  0.1
h1.fm = 0.5

'''
2. Set a análise 
'''
h1.set_analise()

m1 = Condutividade() # modelo material
m1.k11 = 0.31
m1.k22 = 0.51
m1.k33 = 0.91

m2 = Condutividade() # modelo material
m2.k11 = 0.21
m2.k22 = 0.11
m2.k33 = 0.41

m1 = Condutividade() # modelo material
m1.k11 = 0.31
m1.k22 = 0.51
m1.k33 = 0.91

m3 = Condutividade() # modelo material
m3.k11 = 0.10
m3.k22 = 0.11
m3.k33 = 0.09

h1.matH.append(m1)
h1.matH.append(m2)
#h1.matH.append(m3)


'''
3. Desenhe
'''
d.desenha(h1, modelo=MoriTanaka(),  direcao='K11', stats='True')
d.desenha(h1, modelo=Voigt(), direcao='K11', stats='True')
d.desenha(h1, modelo=Reuss(),  direcao='K11', stats='True')
d.desenha(h1, modelo=GSC(),  direcao='K11', stats='True')
d.juntar_grafs(h1, stats='True', direcao='K22', tresh_hold=0.22)
