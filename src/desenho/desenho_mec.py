import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


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

            if len(objH.matH) == 2:
                from desenho.estilos.estilo_registry import EstiloRegistry
                estilo_obj = EstiloRegistry.obter(self.estilo)

                _range = int(objH.fi * 100) if (objH.fi * 100) > 0 else 100
                xs, ys = [], []
                for i in range(0, _range + 1):
                    x, y = estilo_obj.coletar_ponto(objH, modelo, i / 100)
                    xs.append(x)
                    ys.append(y)

                self.nome_modelos.append(label)
                self.graphs.append((xs, ys, label))

                plt.figure()
                estilo_obj.configurar_eixos(plt.gca())
                sns.lineplot(x=xs, y=ys, label=label, color='black')
                sns.despine(left=True)
                if tresh_hold:
                    plt.ylim(tresh_hold)
                if self.estilo == 'poisson':
                    plt.title(f'Coeficiente de Poisson - {label}')
                    plt.xlabel('Fração Volumétrica de Inclusão')
                    plt.ylabel('Coeficiente de Poisson Homogeneizado')
                elif self.estilo == 'normalizar':
                    plt.title(f'Model: {label}')
                    plt.xlabel('fi')
                    plt.ylabel('Eh/Em')
                else:
                    plt.title(f'Model: {label}')
                    plt.xlabel('fi')
                    plt.ylabel('Eh')
                plt.legend()
                plt.show()

                if stats == "True":
                    label_kde = f'Kde: {objH.modH.tipo}'
                    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 10))
                    sns.scatterplot(x=xs, y=ys, ax=axes[0], label=label)
                    sns.kdeplot(ys, ax=axes[1], fill='True', label=label_kde, color='orange')
                    plt.tight_layout(pad=1.08)
                    sns.despine(left=True)
                    plt.legend()

            elif len(objH.matH) == 3:
                self.E = []
                self.x = []
                _range = int(objH.fi * 100) if objH.fi * 100 > 0 else 100

                for i in range(0, _range + 1):
                    Fi = i / 100
                    if self.estilo == 'fixar_fracao_n':
                        self.n_fases(objH, modelo, Fi)
                        plt.title('Módulo E. Homogeinizado vs. FI')
                        plt.xlabel('Fração Volumétrica de Inclusão')
                        plt.ylabel('Módulo de Elásticidade Homogeinizado')

                if self.estilo == "fixar_fracao_n":
                    sns.lineplot(x=self.x, y=self.E, label=label)
                    sns.despine(left=True)
                    self.graphs.append((self.x, self.E, label))

    def n_fases(self, objH, modelo, Fi):
        fiC, fmC = (Fi, Fi - 1)
        objH.analH.fi, objH.analH.fr, objH.analH.fm = (fiC, objH.analH.fr, fmC)
        objH.calc()
        self.E.append(objH.modH.Eh)
        self.x.append(Fi)

    def juntar_grafs(self, objH, estilo=False, stats=False, tresh_hold=None):
        plt.figure()
        if self.estilo == 'poisson':
            plt.title('Coeficiente de Poisson Homogeneizado')
            plt.xlabel('Fração Volumétrica de Inclusão')
            plt.ylabel('Coeficiente de Poisson Homogeneizado')
        elif self.estilo == 'normalizar':
            plt.title('Models')
            plt.xlabel('fi')
            plt.ylabel('Eh/Em')
        else:
            plt.title('Models')
            plt.xlabel('fi')
            plt.ylabel('Eh')

        marcadores = ['o', 's', '^', '*', 'x', 'D', 'p', 'h',
                      '+', '|', '.', ',', '1', '2', '3', '4',
                      '<', '>', 'v']
        for i, graph in enumerate(self.graphs):
            x, y, label = graph
            plt.plot(x, y, label=label, marker=marcadores[i % len(marcadores)], markersize=5)
            plt.legend(loc='best')
            sns.despine(left=True)
            plt.ylim(tresh_hold)

        plt.show()

        if stats == "True":
            for graph in self.graphs:
                x, y, label = graph
                sns.kdeplot(x=y, label=label, alpha=.5, fill=True, bw_method=0.1)
                plt.legend()
                plt.title("Kernel Density")
                sns.despine(left=True)
            plt.show()

    def hist(self, objH, modelos: list):
        kde_values = []
        names = []
        for modelo in modelos:
            objH.modH = modelo
            objH.calc()
            value = float(objH.modH.Eh)
            kde_values.append(value)
            name = objH.modH.tipo
            names.append(name)

        custom_color = ['#033E8C', '#0F5FA6', '#8EBF6B', '#CCD96A', '#04B2D9']
        data = {'Modelos': kde_values}
        df = pd.DataFrame(data, index=names)
        sns.heatmap(data=df, fmt='.4f', cbar_kws={'orientation': 'horizontal'}, annot=True, cmap=custom_color)
        plt.show()
