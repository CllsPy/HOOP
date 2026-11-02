"""Página A4 do HOOP em fpdf2 com o visual do design system.

Usa só as fontes core do PDF (Helvetica, Courier e Symbol), que não precisam
de arquivo de fonte. Elas cobrem apenas Latin-1: ``latin1`` troca traços e o
sinal de menos por equivalentes, e ``escrever`` desenha a letra ν com a fonte
Symbol.
"""
from typing import Optional, Tuple

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from ui.tema import CORES, CORES_FASE

MARGEM = 18.0
TOPO = 26.0
FONTE = 'Helvetica'
FONTE_DADO = 'Courier'
_NU = 'ν'
_SUBSTITUICOES = str.maketrans({'−': '-', '–': '-', '—': '-', '≈': '~', '…': '...'})


def rgb(token: str) -> Tuple[int, int, int]:
    """Cor de um token do DS (ou de uma fase: 'matriz', 'inclusao') em RGB."""
    cor = CORES_FASE.get(token) or CORES[token]
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))


def latin1(texto: str) -> str:
    """Texto que as fontes core aceitam: troca os caracteres fora do Latin-1."""
    return str(texto).translate(_SUBSTITUICOES).encode('latin-1', 'replace').decode('latin-1')


class PaginaHOOP(FPDF):
    """PDF A4 com cabeçalho "HOOP" e "data · p. x de y" em todas as páginas."""

    def __init__(self, data_texto: str):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.data_texto = data_texto
        self.set_margins(left=MARGEM, top=TOPO, right=MARGEM)
        self.set_auto_page_break(auto=True, margin=MARGEM)
        self.set_creator('HOOP')

    @property
    def largura_util(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def header(self) -> None:
        self.set_xy(MARGEM, 10)
        self.set_font(FONTE, 'B', 11)
        self.set_text_color(*rgb('accent'))
        self.cell(30, 6, 'HOOP')
        self.set_font(FONTE, '', 8)
        self.set_text_color(*rgb('ink-muted'))
        texto = f'{self.data_texto} · p. {self.page_no()} de {self.str_alias_nb_pages}'
        self.cell(0, 6, latin1(texto), align='R')
        self.set_draw_color(*rgb('line'))
        self.line(MARGEM, 17, self.w - MARGEM, 17)
        self.set_xy(MARGEM, TOPO)
        self.set_text_color(*rgb('ink'))

    def titulo_secao(self, texto: str) -> None:
        self.set_font(FONTE, 'B', 13)
        self.set_text_color(*rgb('ink'))
        self.cell(0, 8, latin1(texto), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def escrever(self, texto: str, altura: float, estilo: str = '', tamanho: float = 10,
                 cor: str = 'ink') -> None:
        """Escreve na linha atual, a partir de x, trocando para Symbol na letra ν."""
        self.set_text_color(*rgb(cor))
        for i, trecho in enumerate(str(texto).split(_NU)):
            if i:
                self.set_font('Symbol', '', tamanho)
                self.cell(self.get_string_width('n'), altura, 'n')
            if trecho:
                self.set_font(FONTE, estilo, tamanho)
                trecho = latin1(trecho)
                self.cell(self.get_string_width(trecho), altura, trecho)
        self.set_font(FONTE, estilo, tamanho)

    def paragrafo(self, texto: str, tamanho: float = 9, cor: str = 'ink-muted',
                  altura: float = 5) -> None:
        """Parágrafo com quebra de linha, em toda a largura útil."""
        self.set_font(FONTE, '', tamanho)
        self.set_text_color(*rgb(cor))
        self.multi_cell(0, altura, latin1(texto), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def regua(self, cor: str = 'line') -> None:
        """Linha horizontal fina na altura atual."""
        self.set_draw_color(*rgb(cor))
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())

    def celula_dado(self, largura: float, altura: float, texto: str,
                    cor: Optional[str] = None) -> None:
        """Valor numérico em fonte mono, alinhado à direita."""
        self.set_font(FONTE_DADO, '', 10)
        self.set_text_color(*rgb(cor or 'ink'))
        self.cell(largura, altura, latin1(texto), align='R')
