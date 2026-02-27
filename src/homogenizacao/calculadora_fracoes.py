class CalculadoraFracoes:
    """Responsabilidade única: distribuir frações volumétricas pelos materiais.
    Separado de Homogenizacao para permitir teste unitário isolado.
    """

    @staticmethod
    def distribuir(analH, matH) -> None:
        """Atualiza fk de cada fase em matH conforme analH.fi/fm/fr."""
        n = len(matH)
        if n == 2:
            matH[0].fk = 1 - analH.fi
            matH[1].fk = analH.fi
            analH.fm = 1 - analH.fi
        elif n == 3:
            matH[0].fk = analH.fm
            matH[1].fk = analH.fi
            matH[2].fk = 1 - analH.fi - analH.fm
            analH.fr = 1 - analH.fi - analH.fm
        else:
            raise ValueError(
                f"Número de fases não suportado: {n}. Esperado: 2 ou 3."
            )
