from hoop.relatorio.extrator import extrair_dados
from hoop.relatorio.gerador_graficos import gerar_grafico_combinado, gerar_graficos_individuais
from hoop.relatorio.construtor_pdf import construir_pdf


def gerar_relatorio(objH, d, filename: str = 'relatorio.pdf') -> None:
    """Gera um relatório PDF da análise mecânica realizada.

    Args:
        objH:     instancia de Homogenizacao usada em d.desenha()
        d:        instancia de DesenhoMecanico com ao menos uma curva desenhada
        filename: caminho do arquivo PDF de saida (default: 'relatorio.pdf')

    Raises:
        ValueError: se d.graphs estiver vazio ou analise_tipo != 'mecanica'

    Exemplo::

        d.desenha(h1, modelo=GSC())
        d.desenha(h1, modelo=MoriTanaka())
        gerar_relatorio(h1, d, filename='meu_relatorio.pdf')
    """
    if not d.graphs:
        raise ValueError(
            "Nenhum modelo foi plotado. Execute d.desenha() antes de gerar_relatorio()."
        )
    if objH.analise_tipo != 'mecanica':
        raise ValueError(
            f"gerar_relatorio suporta apenas analise_tipo='mecanica'. "
            f"Recebido: '{objH.analise_tipo}'"
        )

    dados = extrair_dados(objH, d)
    img_combinada = gerar_grafico_combinado(dados)
    imgs_individuais = gerar_graficos_individuais(dados)
    construir_pdf(dados, img_combinada, imgs_individuais, filename)
