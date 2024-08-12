class Materiais:
    # SuperClasse de Materiais
    def __init__(self):
        super().__init__()
        self.id = None   # Identificação dos Materiais [1] Matriz [2] Inclusões [3] Interface
        self.tipo = None  # tipo of materials [mechanico], [condutividade]
        self.geo = None  # geometric of inclusions [esfera], [cilindro], [disco]
        self.fk = None   # fração volumétrica da Análise
        self.matTipo = None  # Tipo de material [isotropico]
