from desenho.estilos.estilo_base import EstiloGrafico


class EstiloPoisson(EstiloGrafico):
    nome = 'poisson'
    titulo = 'Coeficiente de Poisson Homogeneizado'
    rotulo_y = 'vh'

    def extrair(self, modelo) -> float:
        return modelo.vh
