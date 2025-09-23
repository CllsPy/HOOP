import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import random
import os
import streamlit as st


class Desenho_Condutividade:
    def __init__(self, estilo):
        self.graphs = []
        self.estilo = estilo

        sns.set_palette('Paired')
        sns.set_style("whitegrid")
        plt.rcParams['font.size'] = 8
        plt.rcParams['figure.figsize'] = (8, 4)

    def desenha(self, objH, modelo, stats=None, direcao=None, tresh_hold=None):
        if not self.estilo:
            self.estilo = 'fixar_fracao'
        if not direcao:
            direcao = 'K11'

        if objH.analise_tipo == 'condutividade':
            objH.modH = modelo
            label = f'Modelo: {objH.modH.tipo}'

            self.K = []
            self.xk = []

            if len(objH.matH) == 2:
                _range = int(objH.fi * 100) if objH.fi * 100 > 0 else 100

                for i in range(_range):
                    Fi = i / 100
                    if self.estilo == 'fixar_fracao':
                        self.fixar_fi(objH, modelo, Fi, direcao)

                if self.estilo == "fixar_fracao":
                    fig, ax = plt.subplots()
                    sns.lineplot(x=self.xk, y=self.K, label=label, ax=ax)
                    ax.set_title('Condutividade')
                    ax.set_xlabel('Fração Volumétrica')
                    ax.set_ylabel(direcao)
                    sns.despine(left=True)
                    st.pyplot(fig)
                    self.graphs.append((self.xk, self.K, label))

                    if stats == "True":
                        label_kde = f'Kde: {objH.modH.tipo}'
                        fig, axes = plt.subplots(1, 2, figsize=(8, 4))
                        sns.scatterplot(x=self.xk, y=self.K, ax=axes[0], label=label)
                        sns.kdeplot(self.K, ax=axes[1], fill=True,
                                    label=label_kde, color='orange')
                        plt.tight_layout(pad=1.08)
                        sns.despine(left=True)
                        if tresh_hold:
                            axes[1].set_ylim(tresh_hold)
                        axes[1].legend()
                        st.pyplot(fig)

            elif len(objH.matH) == 3:
                _range = int(objH.fi * 100) if objH.fi * 100 > 0 else 100

                for i in range(_range):
                    Fi = i / 100
                    if self.estilo == 'fixar_fracao_3':
                        self.fixar_fi_nfases(objH, modelo, Fi, direcao)

                if self.estilo == "fixar_fracao_3":
                    fig, ax = plt.subplots()
                    sns.lineplot(x=self.xk, y=self.K, label=label, ax=ax)
                    ax.set_title('Módulo E. Homogeneizado vs. FI')
                    ax.set_xlabel('Fração Volumétrica de Inclusão')
                    ax.set_ylabel('Módulo de Elasticidade Homogeneizado')
                    sns.despine(left=True)
                    st.pyplot(fig)
                    self.graphs.append((self.xk, self.K, label))

    def fixar_fi_nfases(self, objH, modelo, Fi, direcao):
        if direcao == 'K11':
            direcao_K = objH.modH.K11
        elif direcao == 'K22':
            direcao_K = objH.modH.K22
        else:
            direcao_K = objH.modH.K33

        fiC, fmC = (Fi, Fi - 1)
        objH.analH.fi, objH.analH.fr, objH.analH.fm = (fiC, objH.analH.fr, fmC)
        objH.calc()

        self.K.append(direcao_K)
        self.xk.append(Fi)

    def create_data(self, objH):
        data = pd.DataFrame({'Modelo': objH.modH.tipo,
                             'K': self.K, 'fi': self.xk})

        path = "C:\\Users\\PC\\Desktop\\MLHOOP 1.0\\MLHOOP"
        output = os.path.join(path, f'{objH.modH.tipo}.csv')
        return data.to_csv(output, index=False, encoding='utf-8')

    def fixar_fi(self, objH, modelo, Fi, direcao):
        if direcao == 'K11':
            direcao_K = objH.modH.K11
        elif direcao == 'K22':
            direcao_K = objH.modH.K22
        else:
            direcao_K = objH.modH.K33

        objH.analH.fi, objH.analH.fm = (Fi, Fi - 1)
        objH.calc()
        self.K.append(direcao_K)
        self.xk.append(Fi)

    def juntar_grafs(self, objH, stats=False, direcao=False, tresh_hold=None):
        direcao = direcao.upper() if direcao else "K11"

        fig, ax = plt.subplots()
        ax.set_title('Condutividade')
        ax.set_xlabel('Fração Volumétrica')
        ax.set_ylabel(direcao)

        marcadores = ['o', 's', '^', '*', 'x', 'D', 'p', 'h',
                      '+', '|', '.', ',', '1', '2', '3', '4',
                      '<', '>', 'v']

        for i, graph in enumerate(self.graphs):
            xk, K, label = graph
            ax.plot(xk, K, label=label,
                    marker=marcadores[i % len(marcadores)], markersize=5)

        ax.legend(loc='best')
        sns.despine(left=True)
        if tresh_hold:
            ax.set_ylim(tresh_hold)
        st.pyplot(fig)

        if stats == "True":
            fig, ax = plt.subplots()
            for xk, K, label in self.graphs:
                sns.kdeplot(x=K, fill=True, label=label, alpha=0.5, ax=ax)
            ax.legend()
            ax.set_title("KDE Agrupado")
            sns.despine(left=True)
            st.pyplot(fig)
