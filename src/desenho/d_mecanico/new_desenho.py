import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class Desenho_Mecanico:
    '''
    Classe para plotar modelos mecênicos ou de condutividade.
    '''

    COLORS = ['#033E8C', '#0F5FA6', '#8EBF6B', '#CCD96A', '#04B2D9']
    MARKERS = ['o', 's', '^', '*', 'x', 'D', 'p', 'h', '+', '|', '.', ',', '1', '2', '3', '4', '<', '>', 'v']

    def __init__(self, style='fixar_fracao'):
        self.style = style
        self.graphs = []

        sns.set_palette('Paired')
        sns.set_style("whitegrid")
        plt.rcParams['font.size'] = 8
        plt.rcParams['figure.figsize'] = (8, 4)

    def draw(self, objH=None, model=None, stats=False, threshold=None):
        '''
        M�todo para desenhar os modelos selecionados.
        '''
        if not self.style:
            self.style = 'fixar_fracao'

        if objH.analise_tipo == 'mecanica' and len(objH.matH) == 2:
            label = f'{objH.modH.tipo}'
            self.graphs = []

            for i in range(101):
                Fi = i / 100
                if self.style == 'fixar_fracao':
                    objH.analH.fi, objH.analH.fm = Fi, Fi - 1
                    objH.calc()
                    self.graphs.append((Fi, objH.modH.Eh))

            if self.style == "fixar_fracao":
                xs, Es = zip(*self.graphs)
                plt.plot(xs, Es, label=label, color='black')
                sns.despine(left=True)
                plt.show()

                if stats:
                    label_kde = f'Kde: {objH.modH.tipo}'
                    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 10))
                    sns.scatterplot(x=xs, y=Es, ax=axes[0], label=label)
                    sns.kdeplot(Es, ax=axes[1], fill='True', label=label_kde, color='orange')
                    plt.tight_layout(pad=1.08)
                    sns.despine(left=True)
                    plt.legend()
                    plt.show()

    def join_graphs(self, objH, stats=False, threshold=None):
        '''
        Junta os gráficos.
        '''
        plt.title('Módulo de Elasticidade Homogeneizado')
        plt.xlabel('Fraçãoo')
        plt.ylabel('Eh')

        for i, (xs, Es) in enumerate(self.graphs):
            plt.plot(xs, Es, label=f'Modelo {i}', marker=self.MARKERS[i % len(self.MARKERS)], markersize=5)
            plt.legend(loc='best')
            sns.despine(left=True)
            plt.ylim(threshold)

        plt.show()

        if stats:
            for xs, Es in self.graphs:
                sns.kdeplot(x=Es, alpha=.5, fill=True, bw_method=0.1)
                plt.legend()
                plt.title("Kernel Density")
                sns.despine(left=True)
            plt.show()

    def create_data(self, objH):
        '''
        Gera dados para cada modelo.
        '''
        data = pd.DataFrame({'Modelo': objH.modH.tipo, 'K': self.K, 'fi': self.xk})
        path = "C:\\Users\\PC\\Desktop\MLHOOP 1.0\MLHOOP"
        output = os.path.join(path, f'{objH.modH.tipo}.csv')
        return data.to_csv(output, index=False, encoding='utf-8')

    def report(self):
        '''
        Imprime um relatório com as informações usadas na plotagem.
        '''
        data_models = [{'Modelos': f'Modelo {i}'} for i in range(len(self.graphs))]
        df = pd.DataFrame(data_models)
        df.to_csv('data.csv', index=False)
