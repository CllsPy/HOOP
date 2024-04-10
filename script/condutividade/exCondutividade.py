import sys
from pathlib import Path
from homogenizacao import Homogenizacao
from condutividade import Condutividade
from reuss import Reuss

file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))



h1 = Homogenizacao()
h1.tipo = 'global'
h1.analH.tipo = 'condutividade'
h1.analH.geo = 'esfera'
h1.analH.fi = 0.52
m1 = Condutividade()
m1.k11 = 0.9
m1.k22 = 0.9
m1.k33 = 0.9
m1.geo = h1.geo
m2 = Condutividade()
m2.k11 = 0.025
m2.k22 = 0.05
m2.k33 = 0.025
m2.geo = h1.geo
h1.matH.append(m1)
h1.matH.append(m2)

h1.modH = Reuss()
#h1.analH.desenharCondutividade(h1)
