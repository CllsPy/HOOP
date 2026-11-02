"""Relatório PDF de um ``ResultadoAnalise`` da interface, gerado em memória.

``gerar_pdf(resultado, opcoes)`` devolve os bytes do PDF. A página de dados de
entrada sempre entra; as demais seções dependem de ``OpcoesRelatorio``:
gráfico combinado (1 página), tabela por modelo em fi intermediário e fi máx.
(1 página) e um gráfico por modelo calculado (1 página cada).
``contar_paginas`` diz quantas páginas o PDF terá.
"""
import io
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
from fpdf.enums import XPos, YPos

from hoop.ui.calculo import GRANDEZAS, ResultadoAnalise, abreviar, fracoes, valor_em
from hoop.ui.entrada import (GEOMETRIAS, INCLUSOES, PERSONALIZADO, TIPOS_ANALISE,
                             EntradaComposito, rotulo_material)
from hoop.ui.formatacao import formatar_decimal, formatar_numero
from hoop.ui.pdf_hoop import PaginaHOOP, latin1, rgb
from hoop.ui.graficos import figura_comparacao, figura_modelo_individual, limites_y

FI_INTERMEDIARIO = 0.50
SEM_VALOR = '-'
_DPI_PDF = 200
_ALTURA_LINHA = 8.0
_LARGURA_MODELO = 120.0


@dataclass(frozen=True)
class OpcoesRelatorio:
    """O que entra no PDF. ``grandeza`` é uma chave de ``hoop.ui.calculo.GRANDEZAS``."""
    titulo: str
    autor: str = ''
    grafico_combinado: bool = True
    tabela: bool = True
    graficos_por_modelo: bool = False
    grandeza: str = 'Eh'
    data: date = field(default_factory=date.today)


def titulo_padrao(entrada: EntradaComposito) -> str:
    """Título sugerido: "Concreto com inclusões esféricas"."""
    material = 'Compósito' if entrada.material == PERSONALIZADO else rotulo_material(entrada.material)
    return f'{material} com {INCLUSOES.get(entrada.geometria, entrada.geometria)}'


def nome_arquivo(entrada: EntradaComposito) -> str:
    """Nome do arquivo a partir do material e da geometria: "hoop-concreto-esfera.pdf"."""
    return f'hoop-{entrada.material.replace("_", "-")}-{entrada.geometria}.pdf'


def fi_intermediario(fi_max: float) -> float:
    """fi da coluna do meio da tabela: 0,50, ou metade de fi máx. se ele for menor."""
    return FI_INTERMEDIARIO if fi_max >= FI_INTERMEDIARIO else round(fi_max / 2, 2)


def contar_paginas(resultado: ResultadoAnalise, opcoes: OpcoesRelatorio) -> int:
    """Número de páginas que ``gerar_pdf`` vai produzir com essas opções."""
    individuais = len(resultado.calculados) if opcoes.graficos_por_modelo else 0
    return 1 + int(opcoes.grafico_combinado) + int(opcoes.tabela) + individuais


def imagem_png(fig, dpi: int = _DPI_PDF) -> bytes:
    """PNG de uma figura matplotlib; fecha a figura."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi)
    plt.close(fig)
    return buf.getvalue()


def imagem_comparacao(resultado: ResultadoAnalise, grandeza: str, dpi: int = _DPI_PDF) -> bytes:
    return imagem_png(figura_comparacao(resultado, grandeza), dpi)


def imagem_modelo(resultado: ResultadoAnalise, nome: str, grandeza: str,
                  dpi: int = _DPI_PDF) -> bytes:
    limites = limites_y(resultado, grandeza)
    return imagem_png(figura_modelo_individual(resultado, nome, grandeza, limites), dpi)


def formatar_valor(valor: Optional[float], grandeza: str) -> str:
    if valor is None:
        return SEM_VALOR
    return formatar_numero(valor, GRANDEZAS[grandeza].casas)


def linhas_tabela(resultado: ResultadoAnalise, grandeza: str) -> List[Tuple[str, str, str]]:
    """(modelo abreviado, valor em fi intermediário, valor em fi máx.) para cada modelo."""
    fi_max = resultado.entrada.fi_max
    colunas = (fi_intermediario(fi_max), fi_max)
    return [(abreviar(nome), *(formatar_valor(valor_em(resultado, nome, grandeza, fi), grandeza)
                               for fi in colunas))
            for nome in resultado.curvas]


def legenda_valores(grandeza: str) -> str:
    """Legenda da tabela: "Valores de Eh em MPa."."""
    g = GRANDEZAS[grandeza]
    nome = g.rotulo.split(' [')[0]
    return f'Valores de {nome} em {g.unidade}.' if g.unidade else f'Valores de {nome}.'


def dados_de_entrada(resultado: ResultadoAnalise) -> List[Tuple[str, str, Optional[str]]]:
    """(rótulo, valor, fase) da página 1; fase colore o rótulo ('matriz' ou 'inclusao')."""
    e = resultado.entrada
    pontos = len(fracoes(e.fi_max))
    return [
        ('Tipo de análise', TIPOS_ANALISE.get(e.tipo_analise, e.tipo_analise), None),
        ('Geometria', GEOMETRIAS.get(e.geometria, e.geometria), None),
        ('Em', f'{formatar_numero(e.Em)} MPa', 'matriz'),
        ('νm', formatar_decimal(e.vm), 'matriz'),
        ('Ei', f'{formatar_numero(e.Ei)} MPa', 'inclusao'),
        ('νi', formatar_decimal(e.vi), 'inclusao'),
        ('Faixa de fi', f'0 a {formatar_decimal(e.fi_max)} ({pontos} pontos)', None),
        ('Modelos', ', '.join(abreviar(n) for n in resultado.curvas), None),
    ]


def observacoes(resultado: ResultadoAnalise) -> List[str]:
    """Falhas e limites de validade, no texto que vai abaixo dos dados de entrada."""
    notas = [f'{nome} parou em fi {formatar_decimal(f.fi)}: {f.mensagem}'
             for nome, f in resultado.falhas.items()]
    notas += [f'{c.nome} vale até fi ~ {formatar_decimal(c.fi_validade)}.'
              for c in resultado.curvas.values()
              if c.fi_validade is not None and resultado.entrada.fi_max > c.fi_validade]
    return notas


def _pagina_capa(pdf: PaginaHOOP, resultado: ResultadoAnalise, opcoes: OpcoesRelatorio,
                 numero: int) -> None:
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(*rgb('ink'))
    pdf.multi_cell(0, 9, latin1(opcoes.titulo), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    subtitulo = ' · '.join(filter(None, ('Relatório de homogeneização', opcoes.autor.strip())))
    pdf.paragrafo(subtitulo, tamanho=10)
    pdf.ln(8)
    pdf.titulo_secao(f'{numero}. Dados de entrada')
    for rotulo, valor, fase in dados_de_entrada(resultado):
        _linha_dado(pdf, rotulo, valor, fase)
    notas = observacoes(resultado)
    if notas:
        pdf.ln(6)
        pdf.paragrafo('Observações', cor='ink')
        for nota in notas:
            pdf.paragrafo(nota)


def _linha_dado(pdf: PaginaHOOP, rotulo: str, valor: str, fase: Optional[str]) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.escrever(rotulo, _ALTURA_LINHA, 'B' if fase else '', cor=fase or 'ink-muted')
    pdf.set_x(pdf.l_margin + 50)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(*rgb('ink'))
    pdf.cell(0, _ALTURA_LINHA, latin1(valor), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.regua()


def _pagina_grafico(pdf: PaginaHOOP, resultado: ResultadoAnalise, grandeza: str,
                    numero: int) -> None:
    pdf.add_page()
    pdf.titulo_secao(f'{numero}. Gráfico combinado')
    pdf.image(io.BytesIO(imagem_comparacao(resultado, grandeza)), w=pdf.largura_util)
    pdf.ln(3)
    pdf.set_x(pdf.l_margin)
    pdf.escrever(f'{GRANDEZAS[grandeza].rotulo} em função de fi. Faixa cinza: Voigt-Reuss.',
                 5, tamanho=9, cor='ink-muted')


def _pagina_tabela(pdf: PaginaHOOP, resultado: ResultadoAnalise, grandeza: str,
                   numero: int) -> None:
    pdf.add_page()
    pdf.titulo_secao(f'{numero}. Resultados por modelo')
    fi_max = resultado.entrada.fi_max
    larguras = (60.0, 50.0, 50.0)
    cabecalho = ('Modelo', f'fi {formatar_decimal(fi_intermediario(fi_max))}',
                 f'fi {formatar_decimal(fi_max)}')
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*rgb('ink-muted'))
    for largura, texto, alinhamento in zip(larguras, cabecalho, 'LRR'):
        pdf.cell(largura, _ALTURA_LINHA, latin1(texto), align=alinhamento)
    pdf.ln(_ALTURA_LINHA)
    pdf.regua('line-strong')
    for modelo, meio, maximo in linhas_tabela(resultado, grandeza):
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(*rgb('ink'))
        pdf.cell(larguras[0], _ALTURA_LINHA, latin1(modelo))
        pdf.celula_dado(larguras[1], _ALTURA_LINHA, meio)
        pdf.celula_dado(larguras[2], _ALTURA_LINHA, maximo)
        pdf.ln(_ALTURA_LINHA)
        pdf.regua()
    pdf.ln(3)
    pdf.set_x(pdf.l_margin)
    pdf.escrever(legenda_valores(grandeza), 5, tamanho=9, cor='ink-muted')


def _pagina_modelo(pdf: PaginaHOOP, resultado: ResultadoAnalise, nome: str, grandeza: str,
                   titulo: str) -> None:
    pdf.add_page()
    pdf.titulo_secao(titulo)
    pdf.image(io.BytesIO(imagem_modelo(resultado, nome, grandeza)),
              x=(pdf.w - _LARGURA_MODELO) / 2, w=_LARGURA_MODELO)
    pdf.ln(3)
    fi_max = resultado.entrada.fi_max
    leituras = [f'fi {formatar_decimal(fi)}: '
                f'{formatar_valor(valor_em(resultado, nome, grandeza, fi), grandeza)}'
                for fi in (fi_intermediario(fi_max), fi_max)]
    pdf.set_x(pdf.l_margin)
    pdf.escrever(f'{GRANDEZAS[grandeza].rotulo} em ' + ' · '.join(leituras), 5,
                 tamanho=9, cor='ink-muted')


def gerar_pdf(resultado: ResultadoAnalise, opcoes: OpcoesRelatorio) -> bytes:
    """Gera o relatório em memória e devolve os bytes do PDF.

    Raises:
        ValueError: se nenhum modelo do resultado tiver pontos calculados.
    """
    if not resultado.calculados:
        raise ValueError('Nenhum modelo foi calculado. Calcule a análise antes do relatório.')
    pdf = PaginaHOOP(opcoes.data.strftime('%d/%m/%Y'))
    pdf.set_title(latin1(opcoes.titulo))
    if opcoes.autor.strip():
        pdf.set_author(latin1(opcoes.autor.strip()))
    numero = 1
    _pagina_capa(pdf, resultado, opcoes, numero)
    if opcoes.grafico_combinado:
        numero += 1
        _pagina_grafico(pdf, resultado, opcoes.grandeza, numero)
    if opcoes.tabela:
        numero += 1
        _pagina_tabela(pdf, resultado, opcoes.grandeza, numero)
    if opcoes.graficos_por_modelo:
        numero += 1
        for i, nome in enumerate(resultado.calculados, start=1):
            _pagina_modelo(pdf, resultado, nome, opcoes.grandeza, f'{numero}.{i} {nome}')
    return bytes(pdf.output())
