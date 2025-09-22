import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

class DesenhoMecanico:
    def __init__(self, estilo):
        self.estilo = estilo
        self.graphs = []
        self.nome_modelos = []
        self.instancias_modelos = []

        sns.set_palette('Paired')
        sns.set_style("whitegrid")
        plt.rcParams['font.size'] = 5
        plt.rcParams['figure.figsize'] = (8, 4)

    def desenha(self, objH=None, modelo=None, stats=None, tresh_hold=None):
        if not self.estilo:
            self.estilo = 'fixar_fracao'

        if objH.analise_tipo == 'mecanica':
            objH.modH = modelo
            label = f'{objH.modH.tipo}'

            self.E, self.x, self.vh, self.norm = [], [], [], []

            if len(objH.matH) == 2:
                _range = int(objH.fi * 100) if (objH.fi * 100) > 0 else 100

                for i in range(_range):
                    Fi = i / 100
                    if self.estilo == 'fixar_fracao':
                        self.fixar_fi(objH, modelo, Fi)
                        titulo, xlabel, ylabel = (
                            'Módulo de Elasticidade Homogeneizado',
                            'Fração',
                            'Eh'
                        )
                    elif self.estilo == 'poisson':
                        self.poisson_homo(objH, modelo, Fi)
                        titulo, xlabel, ylabel = (
                            'Poisson Homogeinizado',
                            'Fração Volumétrica de Inclusão',
                            'Coeficiente de Poisson'
                        )
                    elif self.estilo == 'normalizar':
                        self.normalizar(objH, modelo, Fi)
                        titulo, xlabel, ylabel = (
                            'Normalizado',
                            'Fração Vol. Inclusão',
                            'Módulo de Elásticidade : Módulo da Matriz'
                        )

            elif len(objH.matH) == 3:
                _range = int(objH.fi * 100) if objH.fi * 100 > 0 else 100
                for i in range(_range):
                    Fi = i / 100
                    if self.estilo == 'fixar_fracao_n':
                        self.n_fases(objH, modelo, Fi)
                        titulo, xlabel, ylabel = (
                            'Módulo E. Homogeinizado vs. FI',
                            'Fração Volumétrica de Inclusão',
                            'Módulo de Elásticidade Homogeinizado'
                        )
                if self.estilo == "fixar_fracao_n":
                    fig, ax = plt.subplots()
                    sns.lineplot(x=self.x, y=self.E, label=label, ax=ax)
                    sns.despine(left=True)
                    st.pyplot(fig)
                    self.graphs.append((self.x, self.E, label))

            if self.estilo == "fixar_fracao":
                fig, ax = plt.subplots()
                sns.lineplot(x=self.x, y=self.E, label=label, color='black', ax=ax)
                sns.despine(left=True)
                st.pyplot(fig)

                self.nome_modelos.append(label)
                self.graphs.append((self.x, self.E, label))

                if stats == "True":
                    label_kde = f'Kde: {objH.modH.tipo}'
                    fig, axes = plt.subplots(1, 2, figsize=(10, 10))
                    sns.scatterplot(x=self.x, y=self.E, ax=axes[0], label=label)
                    sns.kdeplot(self.E, ax=axes[1], fill=True,
                                label=label_kde, color='orange')
                    plt.tight_layout(pad=1.08)
                    sns.despine(left=True)
                    axes[1].legend()
                    st.pyplot(fig)

            elif self.estilo == "poisson":
                fig, ax = plt.subplots()
                sns.lineplot(x=self.x, y=self.vh, label=label, ax=ax)
                self.graphs.append((self.x, self.vh, label))
                ax.legend()
                sns.despine(left=True)
                if tresh_hold:
                    ax.set_ylim(tresh_hold)
                st.pyplot(fig)

                if stats == "True":
                    label_kde = f'Kde: {objH.modH.tipo}'
                    fig, axes = plt.subplots(1, 2, figsize=(10, 10))
                    sns.scatterplot(x=self.x, y=self.vh, ax=axes[0], label=label)
                    sns.kdeplot(self.vh, ax=axes[1], fill=True,
                                label=label_kde, color='orange')
                    plt.tight_layout(pad=1.08)
                    sns.despine(left=True)
                    axes[1].legend()
                    st.pyplot(fig)

            elif self.estilo == "normalizar":
                fig, ax = plt.subplots()
                sns.lineplot(x=self.x, y=self.norm, label=label, ax=ax)
                self.graphs.append((self.x, self.norm, label))
                ax.legend()
                sns.despine(left=True)
                if tresh_hold:
                    ax.set_ylim(tresh_hold)
                st.pyplot(fig)

                if stats == "True":
                    label_kde = f'Kde: {objH.modH.tipo}'
                    fig, axes = plt.subplots(1, 2, figsize=(10, 10))
                    sns.scatterplot(x=self.x, y=self.norm, ax=axes[0], label=label)
                    sns.kdeplot(self.norm, ax=axes[1], fill=True,
                                label=label_kde, color='orange')
                    plt.tight_layout(pad=1.08)
                    sns.despine(left=True)
                    axes[1].legend()
                    st.pyplot(fig)

    def poisson_homo(self, objH, modelo, Fi):
        objH.analH.fi, objH.analH.fm = (Fi, Fi - 1)
        objH.calc()
        self.vh.append(objH.modH.vh)
        self.x.append(Fi)

    def fixar_fi(self, objH, modelo, Fi):
        objH.analH.fi, objH.analH.fm = (Fi, Fi - 1)
        objH.calc()
        self.E.append(objH.modH.Eh)
        self.x.append(Fi)

    def normalizar(self, objH, modelo, Fi):
        objH.analH.fi, objH.analH.fm = (Fi, Fi - 1)
        objH.calc()
        normal = (objH.modH.Eh / objH.modH.Em)
        self.norm.append(normal)
        self.x.append(Fi)

    def n_fases(self, objH, modelo, Fi):
        fiC, fmC = (Fi, Fi - 1)
        objH.analH.fi, objH.analH.fr, objH.analH.fm = (fiC, objH.analH.fr, fmC)
        objH.calc()
        self.E.append(objH.modH.Eh)
        self.x.append(Fi)

    def juntar_grafs(self, objH, estilo=False, stats=False, tresh_hold=None):
        if self.estilo == 'poisson':
            titulo, xlabel, ylabel = (
                'Coeficiente de Poisson Homogeneizado',
                'Fração Volumétrica de Inclusão',
                'Coeficiente de Poisson Homogeneizado'
            )
        elif self.estilo == 'normalizar':
            titulo, xlabel, ylabel = ('Models', 'fi', 'Eh/Em')
        else:
            titulo, xlabel, ylabel = ('Models', 'fi', 'Eh')

        fig, ax = plt.subplots()
        ax.set_title(titulo)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        marcadores = ['o', 's', '^', '*', 'x', 'D', 'p', 'h',
                      '+', '|', '.', ',', '1', '2', '3', '4',
                      '<', '>', 'v']

        for i, graph in enumerate(self.graphs):
            x, E, label = graph
            ax.plot(x, E, label=label,
                    marker=marcadores[i % len(marcadores)], markersize=5)

        ax.legend(loc='best')
        sns.despine(left=True)
        if tresh_hold:
            ax.set_ylim(tresh_hold)
        st.pyplot(fig)

        if stats == "True":
            fig, ax = plt.subplots()
            for graph in self.graphs:
                x, E, label = graph
                sns.kdeplot(x=E, label=label, alpha=.5, fill=True, bw_method=0.1, ax=ax)
            ax.legend()
            ax.set_title("Kernel Density")
            sns.despine(left=True)
            st.pyplot(fig)

    def hist(self, objH, modelos: list):
        kde_values, names = [], []
        for modelo in modelos:
            objH.modH = modelo
            objH.calc()
            kde_values.append(float(objH.modH.Eh))
            names.append(objH.modH.tipo)

        custom_color = ['#033E8C', '#0F5FA6', '#8EBF6B',
                        '#CCD96A', '#04B2D9']
        data = {'Modelos': kde_values}
        df = pd.DataFrame(data, index=names)

        fig, ax = plt.subplots()
        sns.heatmap(data=df, fmt='.4f', cbar_kws={'orientation': 'horizontal'},
                    annot=True, cmap=custom_color, ax=ax)
        st.pyplot(fig)
