import matplotlib
matplotlib.use('Agg')

import numpy as np
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
from micmodelos.popovic import Popovic
import matplotlib.pyplot as plt


MODELOS = {
    'Voigt': Voigt,
    'Reuss': Reuss,
    'DiluteSuspension': DiluteSuspension,
    'MoriTanaka': MoriTanaka,
    'SelfConsistent': SelfConsistent,
    'GSC': GSC,
    'Popovic': Popovic,
}


st.set_page_config(
    page_title='HOOP: A Python Framework For Composites Analysis',
    layout='wide',
)

with st.sidebar.container(border=True):
    st.subheader('1. Definir Problema')

    estilo = st.selectbox(
        'Selecione o estilo', ['normalizar', 'poisson', 'fixar_fracao']
        )

    tipo = st.selectbox(
        'Selecione o tipo de análise', ['mecanica', 'condutividade']
        )

    geo = st.selectbox(
        'Selecione a geometria', ['esfera']
        )

st.subheader('Etapa 2: Parâmetros')

with st.form('feedback_form'):

    col1, col2 = st.columns(2)

    with col1:
        em = st.number_input('Em [MPa]', min_value=1.0, value=30000.0)
        ei = st.number_input('Ei [MPa]', min_value=1.0, value=70000.0)

    with col2:
        vm = st.number_input('Vm', min_value=0.0, max_value=0.499, value=0.2)
        vi = st.number_input('Vi', min_value=0.0, max_value=0.499, value=0.3)

    models = st.multiselect(
        'Selecione os modelos', list(MODELOS), default=['GSC', 'MoriTanaka']
        )

    submit = st.form_submit_button('Calcular')

if submit:
    if tipo != 'mecanica':
        st.warning('A análise de condutividade ainda não está disponível na interface.')
        st.stop()

    if not models:
        st.warning('Selecione ao menos um modelo.')
        st.stop()

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

    # desenha() abre a própria figura; plt.gcf() a recupera para o Streamlit
    for nome in models:
        try:
            d.desenha(h1, MODELOS[nome]())
        except (ValueError, RuntimeError, np.linalg.LinAlgError) as erro:
            st.error(f'{nome}: {erro}')
            plt.close('all')
            continue

        with st.expander(f'Resposta: {nome}'):
            st.pyplot(plt.gcf())
        plt.close('all')

    if len(d.graphs) > 1:
        d.juntar_grafs(h1)
        st.subheader('Comparação dos modelos')
        st.pyplot(plt.gcf())
        plt.close('all')
