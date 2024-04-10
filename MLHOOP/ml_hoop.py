## Livrarias básicas
import pandas as pd

## sklearn
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.tree import DecisionTreeRegressor

class MLHOOP:
    def __init__(self):
        pass

    '''
    Essa função acessa os dados
    que foram produzidos pelos modelos
    '''
    def pegar_dados(self, url: str):
        dados = pd.read_csv(url)
        return dados

    '''
    Essa classe realiza
    as previsões para os modelos
    '''
    def fazer_previsoes(self, url, valor):
        data = self.pegar_dados(url)
        data = data.dropna()
        X, y = data.drop(['K','Modelo'], axis=1), data['K']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

        dtr = DecisionTreeRegressor() ## modelo escolhido
        grid_search = GridSearchCV(estimator=dtr, param_grid={}, cv=5)
        grid_search.fit(X_train, y_train)
        previsto = grid_search.predict([[valor]])

        print(f'O valor previsto é de {previsto}')

