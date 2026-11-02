from hoop.desenho.desenho_mec import DesenhoMecanico


class DesenhoCondutividade(DesenhoMecanico):
    """Desenho de condutividade homogeneizada numa direção (K11, K22 ou K33).

    Reaproveita o desenho mecânico: só muda o estilo, que extrai a componente
    pedida do tensor de condutividade e exige analise_tipo = 'condutividade'.
    """

    def __init__(self, direcao: str = 'K11'):
        super().__init__(estilo=f'condutividade_{direcao.lower()}')
        self.direcao = direcao.upper()
