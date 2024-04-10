import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


'''
essa classe plota os modelos 
(mecânicos ou condutividade)

estilo: qual estilo de plotagem
'''
class Desenho_Mecanico:
    def __init__(self, estilo):
        self.estilo = estilo # estilo da plotagem

        self.graphs = [] # lista com as informações geradas (e.g Eh, Fi...)
        self.nome_modelos = [] # nome dos modelos para o relatório
        self.instancias_modelos = []

        # detalhes da plotagem seaborn
        sns.set_palette('Paired')
        sns.set_style("whitegrid")
        plt.rcParams['font.size'] = 8
        plt.rcParams['figure.figsize'] = (8, 4)


    '''
    esse método desenha os modelos 
    selecionados.
    
    objH: objeto da classe homogenizacao
    modelo: modelo(s) escolhidos e.g Voigt
    stats: mostrar distribuição (kde)
    tresh_hold:  limite inferior do eixo x 
    '''
    def desenha(self, objH=None, modelo=None, stats=None, tresh_hold=None):
        if self.estilo == False:
            self.estilo = 'fixar_fracao'

        if objH.analise_tipo == 'mecanica':
            objH.modH = modelo # módelo plotado
            label = f'{objH.modH.tipo}' # legenda para a plotagem

            '''
            sempre que uma nova variável
            precisar ser plotado, adicione aqui.
            '''
            self.E = [] # módulo de elasticidade
            self.x = [] # fração
            self.vh = [] # poisson
            self.norm = [] # dados normalizados
            self.Gh = [] # módulo cisalhamento

            ## if para duas fases
            if len(objH.matH) == 2:
                ## ajusta o o número de interações (corrigi)
                _range = int(objH.fi * 100) if (objH.fi * 100) > 0 else 100

                ## numéro de interações
                for i in range(0, _range):
                    Fi = i / 100 # Fi/Fração ou eixo x

                    ## estilo default
                    if self.estilo == 'fixar_fracao':
                        self.fixar_fi(objH, modelo, Fi) # chama a função que faz o cálculo

                        plt.title('Módulo de Elasticidade Homogeneizado') # setta o título
                        plt.xlabel('Fração') # setta informação do eixo x
                        plt.ylabel('Eh') # setta informação do exigo y

                    elif self.estilo == 'poisson': # caso o estilo seja 'poisson'.
                        self.poisson_homo(objH, modelo, Fi) # chama a classe que faz o cálculo

                        plt.title('Poisson Homogeinizado')
                        plt.xlabel('Fração Volumétrica de Inclusão')
                        plt.ylabel('Coeficiente de Poisson')

                    elif self.estilo == 'normalizar': # caso o estilo seja 'poisson'.
                        self.normalizar(objH, modelo, Fi) # chama classe que faz o cálculo

                        plt.title('Normalizado')
                        plt.xlabel('Fração Vol. Inclusão')
                        plt.ylabel('Módulo de Elásticidade : Módulo da Matriz')

            ## esse if plota para o estilo 'fixar_fracao'
            if self.estilo=="fixar_fracao":
                sns.lineplot(x=self.x, y=self.E, label=label, color='black') # plota os valores de x e de E.
                sns.despine(left=True) # remove grade
                plt.show() # mostra a plotagem

                ## guarda o nome do modelo na lista 'nome_modelos' para o relatório
                self.nome_modelos.append(label)
                self.graphs.append((self.x, self.E, label, self.Gh)) ## plota o cisalhamento

                #sns.lineplot(x=self.x, y=self.Gh, color='orange', label=label, marker='+')
                #plt.title("Módulo de Cisalhamento Homogeneizado")
                #sns.despine(left=True)
                #plt.show()

                if stats=="True":
                    label_kde = f'Kde: {objH.modH.tipo}'
                    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 10))
                    sns.scatterplot(x=self.x, y=self.E, ax=axes[0], label=label)
                    sns.kdeplot(self.E, ax=axes[1], fill='True', label=label_kde, color='orange')
                    plt.tight_layout(pad=1.08)
                    sns.despine(left=True)
                    plt.legend()
                    plt.show()

            elif self.estilo=="poisson":
                sns.lineplot(x=self.x, y=self.vh, label=label)
                self.graphs.append((self.x, self.vh, label))
                plt.legend()
                sns.despine(left=True)
                plt.ylim(tresh_hold)
                plt.show()

                if stats=="True":
                    label_kde= f'Kde: {objH.modH.tipo}'
                    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 10))
                    sns.scatterplot(x=self.x, y=self.vh, ax=axes[0], label=label)
                    sns.kdeplot(self.vh, ax=axes[1], fill='True', label=label_kde, color='orange')
                    plt.tight_layout(pad=1.08)
                    sns.despine(left=True)
                    plt.legend()
                    plt.show()

            elif self.estilo == "normalizar":
                sns.lineplot(x=self.x, y=self.norm, label=label)
                self.graphs.append((self.x, self.norm, label))
                plt.legend()
                sns.despine(left=True)
                plt.ylim(tresh_hold)
                plt.show()

                if stats=="True":
                    label_kde= f'Kde: {objH.modH.tipo}'
                    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 10))
                    sns.scatterplot(x=self.x, y=self.norm, ax=axes[0], label=label)
                    sns.kdeplot(self.norm, ax=axes[1], fill='True', label=label_kde, color='orange')
                    plt.tight_layout(pad=1.08)
                    sns.despine(left=True)
                    plt.legend()
                    plt.show()

            # este loop é destinado a plotar modelo de três fases
            elif len(objH.matH) == 3:
                _range = int(objH.fi * 100) if objH.fi * 100 > 0 else 100

                for i in range(0, _range):
                    Fi = i / 100

                    if self.estilo == 'fixar_fracao_3':
                        self.fixar_fi_nfases(objH, modelo, Fi)
                        plt.title('Módulo E. Homogeinizado vs. FI')
                        plt.xlabel('Fração Volumétrica de Inclusão')
                        plt.ylabel('Módulo de Elásticidade Homogeinizado')

                if self.estilo == "fixar_fracao_3":
                    sns.lineplot(x=self.x, y=self.E, label=label)
                    sns.despine(left=True)
                    plt.show()
                    self.graphs.append((self.x, self.E, label, self.Gh))

    '''
    função para plotagem de 
    'n' fases
    '''
    def fixar_fi_nfases(self, objH, modelo, Fi):
        fiC, fmC = (Fi, Fi - 1)
        objH.analH.fi, objH.analH.fr, objH.analH.fm = (fiC, objH.analH.fr, fmC)
        objH.calc()

        self.E.append(objH.modH.Eh)
        self.x.append(Fi)


    def poisson_homo(self, objH, modelo, Fi):
        objH.analH.fi, objH.analH.fm = (Fi, Fi - 1)
        objH.calc()
        self.vh.append(objH.modH.vh) #criar uma variável flexível
        self.x.append(Fi)

    '''
    Essa função é acionada quando o estilo 
    é o 'fixar_fracao'.
    
    objH: objeto da classe homog.
    modelo: modelo usado
    Fi: valor da fração
    '''
    def fixar_fi(self, objH, modelo, Fi):
        objH.analH.fi, objH.analH.fm = (Fi, Fi - 1)
        objH.calc()
        self.E.append(objH.modH.Eh)
        self.x.append(Fi)
        self.Gh.append(objH.modH.Gh) # adicionado recentemente

    def normalizar(self, objH, modelo, Fi):
        objH.analH.fi, objH.analH.fm = (Fi, Fi - 1)
        objH.calc()
        normal = (objH.modH.Eh / objH.modH.Em)
        self.norm.append(normal) #criar variável flexível
        self.x.append(Fi)

    def juntar_grafs(self, objH, estilo=False, stats=False, tresh_hold=None):
        if self.estilo == 'poisson':
            plt.title('Coeficiente de Poisson Homogeneizado')
            plt.xlabel('Fração Volumétrica de Inclusão')
            plt.ylabel('Coeficiente de Poisson Homogeneizado')

        elif self.estilo == 'normalizar':
            plt.title('Coeficiente de Elasticidade Normalizado')
            plt.xlabel('Fração Volumétrica de Inclusão')
            plt.ylabel('Módulo de Elasticidade Homogeneizado / Módulo de Elasticidade da Matriz')

        else:
            plt.title('Módulo de Elasticidade Homogeneizado')
            plt.xlabel('Fração')
            plt.ylabel('Eh')

        i = 0
        for graph in self.graphs:

            i += 1
            marcadores = ['o', 's', '^', '*', 'x', 'D', 'p', 'h',
                          '+', '|', '.', ',', '1', '2', '3', '4',
                          '<', '>', 'v']

            #x, E, label = graph
            x, E, label, _ = graph # para adicionar cisalhamento
            plt.plot(x, E, label=label,  marker=marcadores[i], markersize=5)
            plt.legend(loc='best')
            sns.despine(left=True)
            plt.ylim(tresh_hold)

        plt.show()


        '''
        Essa loop plotar o cisalhamento
        Gh, ative apenas quando necessário.
        
        Transformar em uma condição no futuro.
        '''
        # for graph in self.graphs:
        #     x, E, label, gh = graph
        #
        #     plt.plot(x, gh, label=label, marker=marcadores[i])
        #     plt.legend(loc='best')
        #     sns.despine(left=True)
        #     plt.title("Módulo de Cisalhamento Homogeneizado")
        #     plt.xlabel('Fração')
        #     plt.ylabel('Gh')

        #plt.show()

        if stats == "True":
            for graph in self.graphs:
                x, E, label, gh = graph
                sns.kdeplot(x=E, label=label, alpha=.5, fill=True, bw_method=0.1)
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
        sns.heatmap(data=df, fmt= '.4f', cbar_kws={'orientation':'horizontal'}, annot=True, cmap=custom_color)
        plt.show()
        plt.show()

        #print(df)

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
    Essa função imprime um relatório
    com as informações usadas na plotagem
    '''
    def report(self):
        data_modelos = []
        for modelo in self.nome_modelos:
            data_modelos.append({'Modelos': modelo})

        df = pd.DataFrame(data_modelos)
        df.to_csv('data.csv', index=False)


    def bagg(self):
        mean_eh = []
        E_bag = []
        x_bag = []
        label_bag = []
        for graph in self.graphs:
            x, E, label_, _ = graph
            mean_eh.append(np.mean(E))
            E_bag.append(E)
            x_bag.append(x)
            label_bag.append(label_)

        m_bag = (np.sum(mean_eh)/len(mean_eh))
        plt.boxplot(E_bag, labels=label_bag)
        plt.title(f"Média: {m_bag:.2f}")
        plt.show()
























