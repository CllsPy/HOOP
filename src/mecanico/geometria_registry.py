from mecanico.geometrias import GeometriaEshelby, GeometriaEsfera, GeometriaCilindro, GeometriaDisco
from typing import Dict


class GeometriaRegistry:
    """Registry de geometrias de inclusão. Adicionar nova geometria:
       GeometriaRegistry.registrar(MinhaGeometria())
    """
    _registro: Dict[str, GeometriaEshelby] = {}

    @classmethod
    def registrar(cls, geometria: GeometriaEshelby) -> None:
        cls._registro[geometria.nome] = geometria

    @classmethod
    def obter(cls, nome: str) -> GeometriaEshelby:
        if nome not in cls._registro:
            raise ValueError(
                f"Geometria '{nome}' não registrada. "
                f"Disponíveis: {list(cls._registro.keys())}"
            )
        return cls._registro[nome]

    @classmethod
    def nomes(cls):
        return list(cls._registro.keys())


# Auto-registro das geometrias padrão
GeometriaRegistry.registrar(GeometriaEsfera())
GeometriaRegistry.registrar(GeometriaCilindro())
GeometriaRegistry.registrar(GeometriaDisco())
