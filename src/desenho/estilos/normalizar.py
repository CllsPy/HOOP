from desenho.estilos.estilo_base import EstiloGrafico


class EstiloNormalizar(EstiloGrafico):
    nome = 'normalizar'
    titulo = 'Módulo Normalizado'
    rotulo_y = 'Eh / Em'

    def extrair(self, modelo) -> float:
        return modelo.Eh / modelo.Em
