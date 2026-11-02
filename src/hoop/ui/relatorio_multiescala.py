"""Relatório PDF do concreto multiescala (``ResultadoConcreto``), gerado em memória.

``gerar_pdf_concreto(resultado, opcoes)`` devolve os bytes do PDF. A página 1
traz as fases e as frações por nível e sempre entra; o gráfico por nível com o
erro (1 página) e a tabela de resultados por nível (1 página) são opcionais.
O relatório de duas fases continua em ``hoop.ui.relatorio_analise``.
"""
import io
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Sequence, Tuple

from fpdf.enums import XPos, YPos

from hoop.ui.concreto import (CONSTRUCOES, CONSTRUCOES_MINUSCULAS, FASES_CONCRETO, MODELOS_POROS,
                              ResultadoConcreto, aviso_validade, escolher_destaque,
                              poisson_poros_texto, previa_niveis)
from hoop.ui.formatacao import formatar_decimal, formatar_numero, formatar_percentual
from hoop.ui.graficos import figura_niveis
from hoop.ui.pdf_hoop import PaginaHOOP, latin1, rgb
from hoop.ui.relatorio_analise import imagem_png

SEM_VALOR = '-'
_DPI_PDF = 200
_ALTURA_LINHA = 7.0


@dataclass(frozen=True)
class OpcoesRelatorioConcreto:
    """O que entra no PDF do concreto. A página de dados e frações sempre entra.

    ``destaque`` é o modelo escolhido na Análise (None usa o padrão de
    ``concreto.escolher_destaque``).
    """
    titulo: str
    autor: str = ''
    grafico: bool = True
    tabela: bool = True
    data: date = field(default_factory=date.today)
    destaque: Optional[str] = None


def titulo_padrao_concreto(resultado: ResultadoConcreto) -> str:
    """Título sugerido: "Concreto multiescala com ZTI"."""
    return f'Concreto multiescala {CONSTRUCOES_MINUSCULAS[resultado.entrada.construcao]}'


def nome_arquivo_concreto(resultado: ResultadoConcreto) -> str:
    """"hoop-concreto-multiescala-com-zti.pdf"."""
    return f'hoop-concreto-multiescala-{resultado.entrada.construcao.replace("_", "-")}.pdf'


def contar_paginas_concreto(opcoes: OpcoesRelatorioConcreto) -> int:
    return 1 + int(opcoes.grafico) + int(opcoes.tabela)


def imagem_niveis(resultado: ResultadoConcreto, destaque: Optional[str] = None,
                  dpi: int = _DPI_PDF) -> bytes:
    return imagem_png(figura_niveis(resultado, destaque), dpi)


def dados_concreto(resultado: ResultadoConcreto) -> List[Tuple[str, str, Optional[str]]]:
    """(rótulo, valor, fase) da página 1; fase colore o rótulo (chave de ``CORES_FASE``)."""
    e = resultado.entrada
    linhas = [('Construção', CONSTRUCOES[e.construcao], None),
              ('Modelos', ', '.join(resultado.series), None)]
    for chave, info in FASES_CONCRETO.items():
        f = e.fase(chave)
        linhas.append((info.nome, f'E {formatar_numero(f.E)} MPa · ν {formatar_decimal(f.v)} · '
                                  f'{formatar_percentual(f.fracao, 2)} do concreto', chave))
    poros = (f'{formatar_percentual(e.poros, 2)} dos sólidos (ν {poisson_poros_texto()})'
             if e.poros > 0 else 'Sem poros')
    linhas.append(('Poros', poros, None))
    if e.poros > 0:
        modelo = 'Mori-Tanaka' if e.com_zti else MODELOS_POROS[e.modelo_poros]
        linhas.append(('Modelo dos poros', modelo, None))
    exp = SEM_VALOR if e.E_experimental is None else f'{formatar_numero(e.E_experimental)} MPa'
    linhas.append(('E experimental', exp, None))
    return linhas


def linhas_fracoes(resultado: ResultadoConcreto) -> List[Tuple[str, str, str]]:
    """(nível, fase, fração no nível) de cada fase de cada nível."""
    return [(f'{n.numero} · {n.nome}', f.rotulo, formatar_percentual(f.fracao, 2))
            for n in previa_niveis(resultado.entrada) for f in n.fases]


def linhas_por_nivel(resultado: ResultadoConcreto) -> Tuple[Tuple[str, ...], List[Tuple[str, ...]]]:
    """Cabeçalho e linhas da tabela "E por nível" (MPa), com o erro quando houver E exp."""
    n = resultado.numero_niveis
    com_erro = resultado.entrada.E_experimental is not None
    cabecalho = ('Modelo', *(f'Nível {i}' for i in range(1, n + 1)),
                 *(('Erro',) if com_erro else ()))
    linhas = []
    for nome, serie in resultado.series.items():
        valores = [formatar_numero(nv.resultado.Eh) for nv in serie.niveis]
        linha = [nome, *valores, *([SEM_VALOR] * (n - len(valores)))]
        if com_erro:
            erro = serie.erro_relativo
            linha.append(SEM_VALOR if erro is None else formatar_percentual(erro, 2, sinal=True))
        linhas.append(tuple(linha))
    return cabecalho, linhas


def linhas_propriedades(resultado: ResultadoConcreto) -> List[Tuple[str, ...]]:
    """(modelo, nível, E, ν, K, G) formatados, um por nível calculado."""
    return [(nome, f'{i} · {nv.nome}', formatar_numero(nv.resultado.Eh),
             formatar_numero(nv.resultado.vh, 3), formatar_numero(nv.resultado.kh),
             formatar_numero(nv.resultado.Gh))
            for nome, serie in resultado.series.items()
            for i, nv in enumerate(serie.niveis, start=1)]


def observacoes_concreto(resultado: ResultadoConcreto) -> List[str]:
    notas = []
    for nome, falha in resultado.falhas.items():
        onde = f'no nível {falha.nivel}' if falha.nivel else 'para estes dados'
        notas.append(f'{nome} não foi calculado {onde}: {falha.mensagem}')
    notas += [aviso for aviso in map(lambda n: aviso_validade(resultado, n), resultado.series)
              if aviso]
    return notas


def _linha_dado(pdf: PaginaHOOP, rotulo: str, valor: str, fase: Optional[str]) -> None:
    """Rótulo (na cor da fase) e valor; os dois aceitam a letra ν."""
    pdf.set_x(pdf.l_margin)
    pdf.escrever(rotulo, _ALTURA_LINHA, 'B' if fase else '', cor=fase or 'ink-muted')
    pdf.set_x(pdf.l_margin + 50)
    pdf.escrever(valor, _ALTURA_LINHA)
    pdf.ln(_ALTURA_LINHA)
    pdf.regua()


def _tabela(pdf: PaginaHOOP, cabecalho: Sequence[str], linhas: Sequence[Sequence[str]],
            larguras: Sequence[float], colunas_texto: int = 1) -> None:
    """Tabela simples: as ``colunas_texto`` primeiras em texto, as demais numéricas à direita."""
    pdf.set_x(pdf.l_margin)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*rgb('ink-muted'))
    for i, (largura, texto) in enumerate(zip(larguras, cabecalho)):
        if texto == 'ν':
            x = pdf.get_x()
            pdf.set_x(x + largura - pdf.get_string_width('n') - 1)
            pdf.escrever('ν', _ALTURA_LINHA, 'B', 9, 'ink-muted')
            pdf.set_x(x + largura)
            continue
        pdf.cell(largura, _ALTURA_LINHA, latin1(texto), align='L' if i < colunas_texto else 'R')
    pdf.ln(_ALTURA_LINHA)
    pdf.regua('line-strong')
    for linha in linhas:
        pdf.set_x(pdf.l_margin)
        for i, (largura, texto) in enumerate(zip(larguras, linha)):
            if i < colunas_texto:
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(*rgb('ink'))
                pdf.cell(largura, _ALTURA_LINHA, latin1(texto))
            else:
                pdf.celula_dado(largura, _ALTURA_LINHA, texto)
        pdf.ln(_ALTURA_LINHA)
        pdf.regua()


def _tabela_fracoes(pdf: PaginaHOOP, resultado: ResultadoConcreto) -> None:
    pdf.set_x(pdf.l_margin)
    larguras = (60.0, 60.0, 40.0)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*rgb('ink-muted'))
    for largura, texto, alinhamento in zip(larguras, ('Nível', 'Fase', 'Fração no nível'), 'LLR'):
        pdf.cell(largura, _ALTURA_LINHA, latin1(texto), align=alinhamento)
    pdf.ln(_ALTURA_LINHA)
    pdf.regua('line-strong')
    anterior = None
    for nivel, fase, fracao in linhas_fracoes(resultado):
        pdf.set_x(pdf.l_margin)
        pdf.set_font('Helvetica', 'B' if nivel != anterior else '', 9)
        pdf.set_text_color(*rgb('ink'))
        pdf.cell(larguras[0], _ALTURA_LINHA, latin1(nivel if nivel != anterior else ''))
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(larguras[1], _ALTURA_LINHA, latin1(fase))
        pdf.celula_dado(larguras[2], _ALTURA_LINHA, fracao)
        pdf.ln(_ALTURA_LINHA)
        pdf.regua()
        anterior = nivel


def _pagina_dados(pdf: PaginaHOOP, resultado: ResultadoConcreto,
                  opcoes: OpcoesRelatorioConcreto) -> None:
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(*rgb('ink'))
    pdf.multi_cell(0, 9, latin1(opcoes.titulo), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    subtitulo = ' · '.join(filter(None, ('Relatório de homogeneização multiescala',
                                         opcoes.autor.strip())))
    pdf.paragrafo(subtitulo, tamanho=10)
    pdf.ln(6)
    pdf.titulo_secao('1. Fases e dados de entrada')
    for rotulo, valor, fase in dados_concreto(resultado):
        _linha_dado(pdf, rotulo, valor, fase)
    pdf.ln(6)
    pdf.titulo_secao('2. Frações por nível')
    _tabela_fracoes(pdf, resultado)
    pdf.ln(2)
    pdf.paragrafo('Cada nível usa o resultado do anterior como matriz. Poros em relação aos '
                  'sólidos considerados: poros / (sólidos + poros).')
    notas = observacoes_concreto(resultado)
    if notas:
        pdf.ln(4)
        pdf.paragrafo('Observações', cor='ink')
        for nota in notas:
            pdf.paragrafo(nota)


def _pagina_grafico(pdf: PaginaHOOP, resultado: ResultadoConcreto, numero: int,
                    destaque: Optional[str] = None) -> None:
    pdf.add_page()
    pdf.titulo_secao(f'{numero}. E por nível')
    destaque = escolher_destaque(resultado, destaque)
    pdf.image(io.BytesIO(imagem_niveis(resultado, destaque)), w=pdf.largura_util)
    pdf.ln(3)
    pdf.paragrafo('Módulo de Young homogeneizado em cada nível, uma linha por modelo. '
                  'Tracejado: E experimental.')
    exp = resultado.entrada.E_experimental
    if exp is None:
        return
    pdf.ln(4)
    pdf.paragrafo('Erro relativo ao E experimental', cor='ink', tamanho=10)
    for nome in resultado.series:
        serie = resultado.series[nome]
        erro = serie.erro_relativo
        valor = (SEM_VALOR if erro is None else
                 f'{formatar_numero(serie.Eh)} MPa · {formatar_percentual(erro, 2, sinal=True)}')
        _linha_dado(pdf, nome, valor, None)


def _pagina_tabela(pdf: PaginaHOOP, resultado: ResultadoConcreto, numero: int) -> None:
    pdf.add_page()
    pdf.titulo_secao(f'{numero}. Resultados por nível')
    cabecalho, linhas = linhas_por_nivel(resultado)
    largura_modelo = 50.0
    resto = (pdf.largura_util - largura_modelo) / (len(cabecalho) - 1)
    _tabela(pdf, cabecalho, linhas, (largura_modelo, *([resto] * (len(cabecalho) - 1))))
    pdf.ln(2)
    pdf.paragrafo('Módulo de Young E em MPa. Erro = (E do concreto - E experimental) / '
                  'E experimental.')
    pdf.ln(6)
    pdf.titulo_secao('Propriedades por nível')
    _tabela(pdf, ('Modelo', 'Nível', 'E [MPa]', 'ν', 'K [MPa]', 'G [MPa]'),
            linhas_propriedades(resultado), (36.0, 44.0, 24.0, 18.0, 26.0, 26.0),
           colunas_texto=2)
    pdf.ln(2)
    pdf.paragrafo('K: módulo volumétrico; G: módulo de cisalhamento.')


def gerar_pdf_concreto(resultado: ResultadoConcreto, opcoes: OpcoesRelatorioConcreto) -> bytes:
    """Gera o relatório do concreto em memória e devolve os bytes do PDF.

    Raises:
        ValueError: se nenhum modelo tiver nível calculado.
    """
    if not any(s.niveis for s in resultado.series.values()):
        raise ValueError('Nenhum modelo foi calculado. Calcule a análise antes do relatório.')
    pdf = PaginaHOOP(opcoes.data.strftime('%d/%m/%Y'))
    pdf.set_title(latin1(opcoes.titulo))
    if opcoes.autor.strip():
        pdf.set_author(latin1(opcoes.autor.strip()))
    _pagina_dados(pdf, resultado, opcoes)
    numero = 2
    if opcoes.grafico:
        numero += 1
        _pagina_grafico(pdf, resultado, numero, opcoes.destaque)
    if opcoes.tabela:
        numero += 1
        _pagina_tabela(pdf, resultado, numero)
    return bytes(pdf.output())
