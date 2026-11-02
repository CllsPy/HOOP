import io
from typing import List, Tuple

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from relatorio.extrator import DadosRelatorio

# Cores
_COR_HEADER_BG = (40, 40, 40)
_COR_HEADER_TXT = (255, 255, 255)
_COR_ROW_ALT = (245, 245, 245)
_COR_LINHA = (180, 180, 180)
_COR_SECAO = (230, 80, 20)   # laranja (tema do projeto)


class _PDF(FPDF):
    def header(self):
        self.set_fill_color(*_COR_HEADER_BG)
        self.rect(0, 0, 210, 14, 'F')
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*_COR_HEADER_TXT)
        self.set_y(4)
        self.cell(0, 6, 'HOOP - Relatorio de Analise de Materiais Compositos', align='C')
        self.set_text_color(0, 0, 0)
        self.ln(12)

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, f'Pagina {self.page_no()}', align='C')
        self.set_text_color(0, 0, 0)

    def titulo_secao(self, texto: str):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(*_COR_SECAO)
        self.cell(0, 7, texto, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.set_draw_color(*_COR_SECAO)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_draw_color(0, 0, 0)
        self.ln(3)


def _linha_tabela(pdf: _PDF, col1: str, col2: str, par: bool):
    if par:
        pdf.set_fill_color(*_COR_ROW_ALT)
        fill = True
    else:
        fill = False
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(90, 7, col1, border=1, fill=fill)
    pdf.cell(80, 7, col2, border=1, fill=fill, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _secao_dados_entrada(pdf: _PDF, dados: DadosRelatorio):
    e = dados.entrada
    pdf.titulo_secao('1. Dados de Entrada')

    # Cabeçalho da tabela
    pdf.set_fill_color(*_COR_HEADER_BG)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*_COR_HEADER_TXT)
    pdf.cell(90, 7, 'Parametro', border=1, fill=True)
    pdf.cell(80, 7, 'Valor', border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)

    linhas = [
        ('Tipo de Analise',             e.analise_tipo),
        ('Geometria',                   e.geo),
        ('Estilo de Plot',              e.estilo),
        ('Em - Modulo de Elasticidade (Matriz)',   f'{e.Em:.2f}'),
        ('vm - Coef. de Poisson (Matriz)',         f'{e.vm:.4f}'),
        ('Ei - Modulo de Elasticidade (Inclusao)', f'{e.Ei:.4f}'),
        ('vi - Coef. de Poisson (Inclusao)',       f'{e.vi:.4f}'),
        ('fi max (range simulado)',                f'{e.fi_max:.2f}'),
    ]
    for i, (k, v) in enumerate(linhas):
        _linha_tabela(pdf, k, v, par=(i % 2 == 0))

    pdf.ln(6)


def _secao_grafico_combinado(pdf: _PDF, img_bytes: bytes):
    pdf.titulo_secao('2. Comparacao de Modelos')
    x = pdf.l_margin
    w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.image(io.BytesIO(img_bytes), x=x, w=w)
    pdf.ln(4)


def _secao_resultados_por_modelo(pdf: _PDF,
                                  dados: DadosRelatorio,
                                  imgs_individuais: List[Tuple[str, bytes]]):
    pdf.titulo_secao('3. Resultados por Modelo')

    imgs_map = {nome: img for nome, img in imgs_individuais}

    for modelo in dados.modelos:
        # Verifica espaço — nova página se necessário (aprox. 120mm por bloco)
        if pdf.get_y() > 200:
            pdf.add_page()

        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 7, f'Modelo: {modelo.nome}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

        # Tabela fi=0.5 e fi=max
        idx_meio = len(modelo.xs) // 2
        fi_meio = modelo.xs[idx_meio]
        y_meio = modelo.ys[idx_meio]
        fi_max = modelo.xs[-1]
        y_max = modelo.ys[-1]

        pdf.set_fill_color(*_COR_HEADER_BG)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(*_COR_HEADER_TXT)
        pdf.cell(60, 7, 'Grandeza',        border=1, fill=True)
        pdf.cell(55, 7, f'fi = {fi_meio:.2f}', border=1, fill=True)
        pdf.cell(55, 7, f'fi = {fi_max:.2f} (max)', border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

        pdf.set_font('Helvetica', '', 9)
        pdf.set_fill_color(*_COR_ROW_ALT)
        pdf.cell(60, 7, modelo.y_label, border=1, fill=True)
        pdf.cell(55, 7, f'{y_meio:.6f}',  border=1, fill=True)
        pdf.cell(55, 7, f'{y_max:.6f}',   border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

        # Gráfico individual centralizado
        if modelo.nome in imgs_map:
            w_img = 140
            x_img = (pdf.w - w_img) / 2
            pdf.image(io.BytesIO(imgs_map[modelo.nome]), x=x_img, w=w_img)

        pdf.ln(6)


def construir_pdf(dados: DadosRelatorio,
                  img_combinada: bytes,
                  imgs_individuais: List[Tuple[str, bytes]],
                  filename: str) -> None:
    """Monta e salva o PDF completo."""
    pdf = _PDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(left=15, top=15, right=15)
    pdf.add_page()

    _secao_dados_entrada(pdf, dados)
    _secao_grafico_combinado(pdf, img_combinada)
    pdf.add_page()
    _secao_resultados_por_modelo(pdf, dados, imgs_individuais)

    pdf.output(filename)
