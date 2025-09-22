import matplotlib.pyplot as plt
import streamlit as st

from homogenizacao.homogenizacao import Homogenizacao
from mecanico.mecanico import Mecanico
from desenho.desenho_mec import DesenhoMecanico
from micmodelos.voigt import Voigt
from micmodelos.reuss import Reuss
from micmodelos.dilute import DiluteSuspension
from micmodelos.moritanaka import MoriTanaka
from micmodelos.selfconsistent import SelfConsistent
from micmodelos.gsc import GSC


h1 = Homogenizacao()
d = DesenhoMecanico(estilo='normalizar')

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

h1.calc()

MODELS = [GSC(), SelfConsistent(), MoriTanaka(), DiluteSuspension(), Voigt(), Reuss()]

st.title("Title")

for model in MODELS:
    st.pyplot(d.desenha(h1, modelo=model))

st.pyplot(d.juntar_grafs(h1))
