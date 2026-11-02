from hoop.desenho.estilos.estilo_base import EstiloGrafico

DIRECOES = ('K11', 'K22', 'K33')


class EstiloCondutividade(EstiloGrafico):
    """Condutividade homogeneizada numa direção principal (K11, K22 ou K33)."""

    analise_tipo = 'condutividade'
    titulo = 'Condutividade Homogeneizada'

    def __init__(self, direcao: str):
        direcao = direcao.upper()
        if direcao not in DIRECOES:
            raise ValueError(f"Direção '{direcao}' inválida. Disponíveis: {list(DIRECOES)}")
        self.direcao = direcao

    @property
    def nome(self) -> str:
        return f'condutividade_{self.direcao.lower()}'

    @property
    def rotulo_y(self) -> str:
        return self.direcao

    def extrair(self, modelo) -> float:
        return getattr(modelo, self.direcao)
