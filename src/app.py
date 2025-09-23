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
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(
    page_title="Homogenização de Compósitos",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhor visualização
st.markdown("""
    <style>
    .stAlert {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
    }
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
        padding-left: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Título principal
st.markdown("<h1 class='main-header'>🔬 Sistema de Homogenização de Compósitos</h1>", unsafe_allow_html=True)
st.markdown("---")

# Inicialização de objetos
if 'homogenizacao' not in st.session_state:
    st.session_state.homogenizacao = Homogenizacao()
    st.session_state.desenho = DesenhoMecanico(estilo='normalizar')

h1 = st.session_state.homogenizacao
d = st.session_state.desenho

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configurações Gerais")
    st.info("Configure os parâmetros do seu modelo de homogenização seguindo as etapas abaixo.")
    
    # ETAPA 1: Configurações básicas
    st.markdown("### 📋 Etapa 1: Tipo de Análise")
    with st.expander("ℹ️ Instruções", expanded=True):
        st.write("""
        Defina o tipo de análise e a geometria do reforço:
        - **Tipo de homogenização**: Define o escopo da análise
        - **Tipo de análise**: Define as propriedades a serem calculadas
        - **Geometria**: Forma do material de reforço
        """)
    
    tipo_homo = st.selectbox(
        "Tipo de homogenização",
        ["global", "local"],
        help="Global: análise do compósito completo | Local: análise pontual"
    )
    
    analise_tipo = st.selectbox(
        "Tipo de análise",
        ["mecanica", "termica", "eletrica"],
        help="Selecione o tipo de propriedade a ser homogeneizada"
    )
    
    geometria = st.selectbox(
        "Geometria do reforço",
        ["esfera", "fibra", "elipsoide", "disco"],
        help="Forma geométrica das inclusões no compósito"
    )
    
    st.markdown("---")
    
    # ETAPA 2: Propriedades da matriz
    st.markdown("### 🔷 Etapa 2: Propriedades da Matriz")
    with st.expander("ℹ️ Instruções", expanded=False):
        st.write("""
        Configure as propriedades do material da matriz:
        - **Módulo de Young (Em)**: Rigidez do material em MPa
        - **Coeficiente de Poisson (νm)**: Razão entre deformações (0 < ν < 0.5)
        """)
    
    col1, col2 = st.columns(2)
    with col1:
        Em = st.number_input(
            "Módulo de Young - Em (MPa)",
            min_value=0.1,
            max_value=1000000.0,
            value=41000.0,
            step=1000.0,
            help="Módulo elástico da matriz"
        )
    
    with col2:
        vm = st.number_input(
            "Coef. Poisson - νm",
            min_value=0.0,
            max_value=0.499,
            value=0.2,
            step=0.01,
            format="%.3f",
            help="Coeficiente de Poisson da matriz"
        )
    
    st.markdown("---")
    
    # ETAPA 3: Propriedades da inclusão
    st.markdown("### 🔶 Etapa 3: Propriedades da Inclusão")
    with st.expander("ℹ️ Instruções", expanded=False):
        st.write("""
        Configure as propriedades do material de reforço/inclusão:
        - **Módulo de Young (Ei)**: Rigidez da inclusão em MPa
        - **Coeficiente de Poisson (νi)**: Razão entre deformações
        - **Fração volumétrica**: Porcentagem de volume ocupado pelas inclusões
        """)
    
    col3, col4 = st.columns(2)
    with col3:
        Ei = st.number_input(
            "Módulo de Young - Ei (MPa)",
            min_value=0.001,
            max_value=1000000.0,
            value=0.1,
            step=0.1,
            help="Módulo elástico da inclusão"
        )
    
    with col4:
        vi = st.number_input(
            "Coef. Poisson - νi",
            min_value=0.0,
            max_value=0.499,
            value=0.2,
            step=0.01,
            format="%.3f",
            help="Coeficiente de Poisson da inclusão"
        )
    
    frac_vol = st.slider(
        "Fração volumétrica (%)",
        min_value=0.0,
        max_value=100.0,
        value=30.0,
        step=1.0,
        help="Percentual do volume total ocupado pelas inclusões"
    )
    
    st.markdown("---")
    
    # ETAPA 4: Seleção de modelos
    st.markdown("### 📊 Etapa 4: Modelos de Homogenização")
    with st.expander("ℹ️ Instruções", expanded=False):
        st.write("""
        Selecione os modelos de homogenização para comparação:
        - **Voigt/Reuss**: Limites superior e inferior
        - **Mori-Tanaka**: Modelo para inclusões alinhadas
        - **Self-Consistent**: Modelo iterativo
        - **GSC**: Generalized Self-Consistent
        - **Dilute Suspension**: Para baixas frações volumétricas
        """)

# Área principal
# Aplicar configurações
h1.tipo = tipo_homo
h1.analise_tipo = analise_tipo
h1.geo = geometria
h1.Em = Em
h1.vm = vm
h1.Ei = Ei
h1.vi = vi

# Configurar análise
h1.set_analise()

# Criar materiais
m1 = Mecanico()
m1.E = h1.Em
m1.v = h1.vm
m1.geo = h1.analH.geo

m2 = Mecanico()
m2.E = h1.Ei
m2.v = h1.vi
m2.geo = h1.analH.geo

# Limpar e adicionar materiais
h1.matH.clear()
h1.matH.append(m1)
h1.matH.append(m2)

# Lista de modelos disponíveis
MODELS = [GSC(), SelfConsistent(), MoriTanaka(), DiluteSuspension(), Reuss(), Voigt()]
NOMES = [m.tipo for m in MODELS]

# Interface principal
col_main1, col_main2 = st.columns([2, 1])

with col_main1:
    st.markdown("<h2 class='step-header'>📈 Visualização dos Resultados</h2>", unsafe_allow_html=True)
    
    # Seleção de modelos
    modelos_selecionados = st.multiselect(
        "Selecione os modelos para análise:",
        NOMES,
        default=["GSC", "Mori-Tanaka", "Voigt", "Reuss"][:min(4, len(NOMES))],
        help="Escolha múltiplos modelos para comparação"
    )
    
    if modelos_selecionados:
        # Tabs para diferentes visualizações
        tab1, tab2, tab3 = st.tabs(["📊 Comparação Individual", "📈 Análise Comparativa", "📋 Resumo"])
        
        with tab1:
            st.info("Cada gráfico mostra o comportamento do módulo efetivo em função da fração volumétrica para o modelo selecionado.")
            
            # Grid de gráficos individuais
            cols = 2
            linhas = (len(modelos_selecionados) + cols - 1) // cols
            
            idx = 0
            for _ in range(linhas):
                col_objs = st.columns(cols)
                for col in col_objs:
                    if idx < len(modelos_selecionados):
                        nome = modelos_selecionados[idx]
                        modelo = next(m for m in MODELS if m.tipo == nome)
                        with col:
                            st.markdown(f"**{nome}**")
                            d.desenha(h1, modelo=modelo)
                        idx += 1
        
        with tab2:
            st.info("Gráfico comparativo mostrando todos os modelos selecionados em uma única visualização.")
            d.juntar_grafs(h1, modelos_selecionados)
        
        with tab3:
            st.markdown("### 📊 Propriedades Efetivas Calculadas")
            
            # Tabela de resultados
            results_data = []
            for nome in modelos_selecionados:
                modelo = next(m for m in MODELS if m.tipo == nome)
                # Aqui você precisaria calcular os valores efetivos
                # Este é um exemplo placeholder
                results_data.append({
                    "Modelo": nome,
                    "E_efetivo (MPa)": f"{Em * (1 - frac_vol/100) + Ei * frac_vol/100:.2f}",
                    "ν_efetivo": f"{vm * (1 - frac_vol/100) + vi * frac_vol/100:.3f}"
                })
            
            st.dataframe(results_data, use_container_width=True)
    else:
        st.warning("⚠️ Por favor, selecione pelo menos um modelo de homogenização.")

with col_main2:
    st.markdown("<h2 class='step-header'>📝 Resumo dos Parâmetros</h2>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("### Configuração Atual")
        st.markdown(f"""
        **Análise:**
        - Tipo: `{tipo_homo}`
        - Propriedade: `{analise_tipo}`
        - Geometria: `{geometria}`
        
        **Matriz:**
        - E = {Em:.1f} MPa
        - ν = {vm:.3f}
        
        **Inclusão:**
        - E = {Ei:.3f} MPa
        - ν = {vi:.3f}
        - Fração Vol. = {frac_vol:.1f}%
        
        **Razão E_i/E_m:** {Ei/Em:.4f}
        """)
        
        # Indicador de contraste
        razao = Ei/Em
        if razao < 0.01:
            st.error("Contraste muito alto (inclusão muito mole)")
        elif razao < 0.1:
            st.warning("Contraste alto")
        elif 0.1 <= razao <= 10:
            st.success("Contraste moderado")
        elif razao > 100:
            st.error("Contraste muito alto (inclusão muito rígida)")
        else:
            st.warning("Contraste alto")

# Rodapé
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>Sistema de Homogenização de Compósitos | Desenvolvido para Pesquisadores</small>
</div>
""", unsafe_allow_html=True)