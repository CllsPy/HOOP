class CalculadoraFracoes:
    """Responsabilidade única: distribuir frações volumétricas pelos materiais.
    Separado de Homogenizacao para permitir teste unitário isolado.
    """

    @staticmethod
    def distribuir(analH, matH) -> None:
        """Atualiza fk da matriz (matH[0]) e da inclusão (matH[1]) a partir de analH.fi.

        Só compósitos de 2 fases são suportados: todos os modelos micromecânicos
        leem apenas matH[0] (matriz) e matH[1] (inclusão).
        """
        if len(matH) != 2:
            raise ValueError(
                f"Número de fases não suportado: {len(matH)}. Apenas compósitos de "
                "2 fases (matriz + inclusão) são suportados, pois nenhum modelo "
                "micromecânico lê uma terceira fase."
            )
        matH[0].fk = 1 - analH.fi
        matH[1].fk = analH.fi
        analH.fm = 1 - analH.fi
