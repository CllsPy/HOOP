from homogenizacao.homogenizacao import Homogenizacao
from mecanico.mecanico import Mecanico
from desenho.desenho_mec import DesenhoMecanico

from micmodelos.voigt import Voigt
from micmodelos.reuss import Reuss
from micmodelos.dilute import DiluteSuspension
from micmodelos.moritanaka import MoriTanaka
from micmodelos.selfconsistent import SelfConsistent
from micmodelos.gsc import GSC

# Inicializar com parâmetros
h1 = Homogenizacao(
    geo="esfera",
    fi=0.6,  # definir fração volumétrica da fibra/inclusão
    fm=0.4,  # fração da matriz
    analise_tipo="global",
    material_tipo="mecanica"
)

m1 = Mecanico(E=41000, v=0.2, geo=h1.geo)  # matriz
m2 = Mecanico(E=0.1, v=0.2, geo=h1.geo)    # inclusão

h1.materiais.append(m1)
h1.materiais.append(m2)

h1.modelo = MoriTanaka()

h1.calc()

print(f"Eh (homogeneizado): {h1.modelo.Eh}")
print(f"Em (matriz): {h1.modelo.Em}")
print(f"Ei (inclusão): {h1.modelo.Ei}")
print(f"vh (Poisson homog.): {h1.modelo.vh}")

#d = DesenhoMecanico(estilo='normalizar')
#d.desenha(h1, modelo=MoriTanaka())
