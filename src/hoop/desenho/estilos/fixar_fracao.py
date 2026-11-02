from hoop.desenho.estilos.estilo_base import EstiloGrafico


class EstiloFixarFracao(EstiloGrafico):
    nome = 'fixar_fracao'
    titulo = 'Módulo de Elasticidade Homogeneizado'
    rotulo_y = 'Eh'

    def extrair(self, modelo) -> float:
        return modelo.Eh
