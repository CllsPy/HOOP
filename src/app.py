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
from PIL import Image
import matplotlib.pyplot as plt


st.set_page_config(
    page_title='HOOP: A Python Framework For Composites Analysis',
    layout='wide',
)

with st.sidebar.container(border=True):
    st.subheader('1. Definir Problema')

    estilo = st.selectbox(
        'Selecione o estilo', ['normalizar','poisson', 'fixar_fracao']
        )


    tipo = st.selectbox(
        'Selecione o tipo de análise', ['mecanica', 'condutividade']
        )

    geo = st.selectbox(
        'Selecione a geometria', ['esfera']
        )

st.subheader('Etapa 2: Parâmetros')
import streamlit as st

with st.form('feedback_form'):

    col1, col2 = st.columns(2)

    with col1:
        em = st.number_input('Em')
        ei = st.number_input('Ei')

    with col2:    
        vm = st.number_input('Vm')
        vi = st.number_input('Vi')
    


    models = st.multiselect(
    'Selecione os modelos', ['GSC', 'MoriTanaka', 'DiluteSuspension']
    )

    try: 
        submit = st.form_submit_button('Computer')

        h1 = Homogenizacao()
        d = DesenhoMecanico(estilo=estilo)

        h1.tipo = "global"
        h1.analise_tipo = tipo
        h1.geo = geo

        h1.Em = em
        h1.vm = vm

        h1.vi = vi
        h1.Ei = ei

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

        
        for value in models:
            if value == 'GSC':
                gsc = GSC()
            
                fig, ax = plt.subplots()
                d.desenha(h1, gsc)

                with st.expander("Resposta"):
                    st.pyplot(fig)
    
    except:
        'Por Favor, Insira Dados Válidos!'




#b = d.desenha(h1, modelo=SelfConsistent())
#c = d.desenha(h1, modelo=MoriTanaka())
#d = d.desenha(h1, modelo=DiluteSuspension())
#st.pyplot(a)
