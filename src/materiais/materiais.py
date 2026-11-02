class Materiais:
    """Superclasse dos materiais (fases) de um compósito."""

    def __init__(self):
        super().__init__()
        self.id = None       # Identificação da fase (em matH: [0] matriz, [1] inclusão, [2] terceira fase)
        self.tipo = None     # Tipo de análise: 'mecanico' ou 'condutividade'
        self.geo = None      # Geometria das inclusões: 'esfera', 'cilindro' ou 'disco'
        self.fk = None       # Fração volumétrica da fase
        self.matTipo = None  # Simetria do material: 'isotropico'
