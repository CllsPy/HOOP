import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import random
import os


class Desenho_Condutividade:
    def __init__(self, estilo):
        self.graphs = []
        self.estilo = estilo

        sns.set_palette('Paired')
        sns.set_style("whitegrid")
        plt.rcParams['font.size'] = 8
        plt.rcParams['figure.figsize'] = (8, 4)

    '''
    Essa função desenha um gráfico fi por K
    para condutividade
    
    Recebe:
    - Objeto 
    - Modelo
    - Estilo
    - Direção
    
    O resto é opcional
    '''
    def desenha(self, objH, modelo, stats=None,  direcao=None, tresh_hold=None):
        if self.estilo == False: self.estilo = 'fixar_fracao'
        elif direcao == False: direcao = 'K11'

        if objH.analise_tipo == 'condutividade':
            objH.modH = modelo
            label = f'Modelo: {objH.modH.tipo}'

            self.K = []
            self.xk = []


            if len(objH.matH) == 2:
                _range = int(objH.fi * 100) if objH.fi * 100 > 0 else 100

                for i in range(0, _range):
                    Fi = i / 100
                    if self.estilo == 'fixar_fracao':
                        self.fixar_fi(objH, modelo, Fi, direcao)
                        plt.title('Condutividade')
                        plt.xlabel('Fração Volumétrica')
                        plt.ylabel(direcao)

            if self.estilo=="fixar_fracao":

                sns.lineplot(x = self.xk, y = self.K, label=label)
                sns.despine(left=True)
                plt.show()
                self.graphs.append((self.xk, self.K, label))


                if stats=="True":
                    label_kde= f'Kde: {objH.modH.tipo}'
                    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(8, 4))
                    sns.scatterplot(x=self.xk, y=self.K, ax=axes[0], label=label)
                    sns.kdeplot(self.K, ax=axes[1], fill='True', label=label_kde, color='orange')
                    plt.tight_layout(pad=1.08)
                    sns.despine(left=True)
                    plt.legend()
                    plt.ylim(tresh_hold)
                    plt.show()

            # este loop é destinado a plotar modelo de três fases
            elif len(objH.matH) == 3:
                    _range = int(objH.fi * 100) if objH.fi * 100 > 0 else 100

                    for i in range(0, _range):
                        Fi = i / 100

                        if self.estilo == 'fixar_fracao_3':
                            self.fixar_fi_nfases(objH, modelo, Fi, direcao)
                            plt.title('Módulo E. Homogeinizado vs. FI')
                            plt.xlabel('Fração Volumétrica de Inclusão')
                            plt.ylabel('Módulo de Elásticidade Homogeinizado')

                    if self.estilo == "fixar_fracao_3":
                        sns.lineplot(x=self.xk, y=self.K, label=label)
                        sns.despine(left=True)
                        plt.show()
                        self.graphs.append((self.xk, self.K, label))

        '''
        função para plotagem de 
        'n' fases
        '''

    def fixar_fi_nfases(self, objH, modelo, Fi, direcao):
        if direcao == 'K11': direcao_K = objH.modH.K11
        elif direcao == 'K22': direcao_K = objH.modH.K22
        else: direcao_K = objH.modH.K33

        fiC, fmC = (Fi, Fi - 1)
        objH.analH.fi, objH.analH.fr, objH.analH.fm = (fiC, objH.analH.fr, fmC)
        objH.calc()

        self.K.append(direcao_K)
        self.xk.append(Fi)


    '''
    Essa função gera dados
    para cada modelo, quando chamada
    abaixo dele.
    '''
    def create_data(self, objH):
        data = pd.DataFrame({'Modelo':objH.modH.tipo,
                             'K': self.K, 'fi':self.xk})


        path = "C:\\Users\\PC\\Desktop\MLHOOP 1.0\MLHOOP"
        output = os.path.join(path,  f'{objH.modH.tipo}.csv')
        return data.to_csv(output, index=False, encoding='utf-8')


    '''
    Essa função gera um gráfico default, 
    apenas fi por K (K11, K22, K33)
    '''
    def fixar_fi(self, objH, modelo, Fi, direcao):
        if direcao == 'K11': direcao_K = objH.modH.K11
        elif direcao == 'K22': direcao_K = objH.modH.K22
        else: direcao_K = objH.modH.K33

        objH.analH.fi, objH.analH.fm = (Fi, Fi - 1)
        objH.calc()
        self.K.append(direcao_K)
        self.xk.append(Fi)

    '''
    Essa função junta todos os
    modelos plotados anteriomente.
    '''
    def juntar_grafs(self, objH, stats=False, direcao=False, tresh_hold=None):
        direcao = direcao.upper()

        plt.title('Condutividade')
        plt.xlabel('Fração Volumétrica')
        plt.ylabel(direcao)

        i = 0
        dfs = []

        for graph in self.graphs:
            i += 1
            marcadores = ['o', 's', '^', '*', 'x', 'D', 'p', 'h',
                          '+', '|', '.', ',', '1', '2', '3', '4',
                          '<', '>', 'v']

            xk, K, label = graph
            plt.plot(xk, K, label=label,  marker=marcadores[i], markersize=5)
            plt.legend(loc='best')
            sns.despine(left=True)
            plt.ylim(tresh_hold)

        plt.show()



        if stats == "True":
            for graph in self.graphs:
                xk, K, label = graph
                sns.kdeplot(x=K, fill=True, palette="Set1", label=label)
                plt.legend()
                plt.title("KDE Agrupado")
                sns.despine(left=True)

            plt.show()

