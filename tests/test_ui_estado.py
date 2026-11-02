import pathlib
import re
from dataclasses import replace

import matplotlib.pyplot as plt
import numpy as np
import pytest

from hoop.exemplos import MATERIAIS
from hoop.resultados.resultados import ResultadoMecanico
from hoop.ui import calculo
from hoop.ui.calculo import (GRANDEZAS, MODELOS, MODELOS_PADRAO, InfoModelo, abreviar, calcular,
                             escolher_referencia, fracoes, valor_em)
from hoop.ui.entrada import (PERSONALIZADO, PRESETS, EntradaComposito, aplicar_preset,
                             preset_correspondente, resumo_entrada, validar)
from hoop.ui.formatacao import (formatar_decimal, formatar_numero, formatar_percentual,
                                interpretar_numero)
from hoop.ui.graficos import figura_comparacao, figura_modelo_individual, limites_y

CONCRETO_FI_030 = {
    'Voigt': 42_339, 'Reuss': 36_207, 'Mori-Tanaka': 38_235,
    'Self-Consistent': 38_578, 'GSC': 38_272,
}


@pytest.fixture(scope='module')
def resultado_concreto():
    return calcular(EntradaComposito())


@pytest.fixture(autouse=True)
def fechar_figuras():
    yield
    plt.close('all')


@pytest.mark.parametrize('chave', list(PRESETS))
def test_presets_batem_com_materiais_dos_cases(chave):
    p = PRESETS[chave]
    assert dict(Em=p.Em, vm=p.vm, Ei=p.Ei, vi=p.vi) == MATERIAIS[chave]


def test_entrada_padrao_e_concreto_com_cinco_modelos():
    e = EntradaComposito()
    assert preset_correspondente(e) == 'concreto'
    assert e.modelos == MODELOS_PADRAO == ('Voigt', 'Reuss', 'Mori-Tanaka', 'Self-Consistent', 'GSC')
    assert resumo_entrada(e) == 'Concreto · esfera · 5 modelos'
    assert validar(e) == {}


def test_aplicar_preset_e_personalizado():
    e = aplicar_preset(EntradaComposito(), 'epoxy_vidro')
    assert (e.Em, e.Ei, e.material) == (3_500, 73_000, 'epoxy_vidro')
    assert preset_correspondente(replace(e, Em=3_600)) == PERSONALIZADO


@pytest.mark.parametrize('campo, valor', [
    ('vm', 0.5), ('vi', 0.6), ('vm', -0.1), ('Em', 0.0), ('Ei', -5.0),
    ('modelos', ()), ('fi_max', 0.0), ('fi_max', 1.2),
    ('geometria', 'cilindro'), ('tipo_analise', 'condutividade'),
    ('vm', float('nan')), ('Em', float('inf')), ('Ei', float('nan')),
])
def test_validar_aponta_o_campo_invalido(campo, valor):
    erros = validar(replace(EntradaComposito(), **{campo: valor}))
    assert list(erros) == [campo]


def test_mensagem_de_poisson_diz_como_corrigir():
    msg = validar(replace(EntradaComposito(), vm=0.5))['vm']
    assert msg.startswith('Use um valor menor que 0,5.')


@pytest.mark.parametrize('valor, casas, esperado', [
    (30000, 0, '30 000'), (38235.29, 0, '38 235'), (1234567.891, 2, '1 234 567,89'),
    (0.3, 2, '0,30'), (-5.3, 1, '−5,3'),
])
def test_formatar_numero(valor, casas, esperado):
    assert formatar_numero(valor, casas) == esperado


def test_formatar_decimal_e_percentual():
    assert formatar_decimal(0.3, 2) == '0,30'
    assert formatar_percentual(0.274) == '27,4%'
    assert formatar_percentual(0.107, sinal=True) == '+10,7%'
    assert formatar_percentual(-0.053, sinal=True) == '−5,3%'


@pytest.mark.parametrize('texto, esperado', [
    ('30 000', 30000.0), ('30e3', 30000.0), ('0,3', 0.3), ('0.3', 0.3), ('abc', None),
    ('nan', None), ('inf', None), ('-inf', None), ('1e999', None),
])
def test_interpretar_numero(texto, esperado):
    assert interpretar_numero(texto) == esperado


def test_fracoes_tem_passo_001():
    assert len(fracoes(1.0)) == 101
    assert len(fracoes(0.5)) == 51
    assert fracoes(0.5)[-1] == pytest.approx(0.5)


@pytest.mark.parametrize('modelo', list(CONCRETO_FI_030))
def test_calcular_concreto_bate_valores_conhecidos(resultado_concreto, modelo):
    assert valor_em(resultado_concreto, modelo, 'Eh', 0.30) == pytest.approx(
        CONCRETO_FI_030[modelo], abs=1)


def test_calcular_devolve_tres_grandezas_e_avisa_progresso():
    chamadas = []
    r = calcular(EntradaComposito(modelos=('Mori-Tanaka', 'Dilute Suspension')),
                 ao_progredir=lambda *a: chamadas.append(a))
    assert chamadas == [('Mori-Tanaka', 0, 2), ('Dilute Suspension', 1, 2)]
    mt = r.curvas['Mori-Tanaka']
    assert set(mt.valores) == {'Eh', 'Eh/Em', 'vh'}
    assert np.allclose(mt.valores['Eh/Em'], mt.valores['Eh'] / 30_000)
    assert r.falhas == {}
    dilute = r.curvas['Dilute Suspension']
    assert dilute.fi_validade == pytest.approx(0.10)
    assert dilute.valido_em(0.10) and not dilute.valido_em(0.11)


class ModeloQueFalha:
    def homogeneizar(self, composito):
        fi = composito.fi
        if fi > 0.855:
            raise ValueError('Sem raiz real.')
        return ResultadoMecanico(Eh=30_000 * (1 + fi), vh=0.2, Em=30_000, fi=fi)


def test_falha_parcial_guarda_curva_ate_o_ponto(monkeypatch):
    monkeypatch.setitem(MODELOS, 'Falso', InfoModelo('Falso', ModeloQueFalha, 'Teste', ''))
    r = calcular(EntradaComposito(modelos=('Mori-Tanaka', 'Falso')))

    assert list(r.falhas) == ['Falso']
    assert r.falhas['Falso'].fi == pytest.approx(0.86)
    assert r.falhas['Falso'].mensagem == 'Sem raiz real.'
    assert r.curvas['Falso'].fis[-1] == pytest.approx(0.85)
    assert valor_em(r, 'Falso', 'Eh', 0.5) == pytest.approx(45_000)
    assert valor_em(r, 'Falso', 'Eh', 0.9) is None
    assert len(r.curvas['Mori-Tanaka'].fis) == 101
    assert r.calculados == ('Mori-Tanaka', 'Falso')


def test_valor_em_interpola_e_ignora_modelo_ausente(resultado_concreto):
    a = valor_em(resultado_concreto, 'Voigt', 'Eh', 0.30)
    b = valor_em(resultado_concreto, 'Voigt', 'Eh', 0.31)
    assert a < valor_em(resultado_concreto, 'Voigt', 'Eh', 0.305) < b
    assert valor_em(resultado_concreto, 'Popovic', 'Eh', 0.3) is None


def test_erros_de_modelo_incluem_os_do_dominio():
    assert np.linalg.LinAlgError in calculo.ERROS_DE_MODELO


@pytest.mark.parametrize('grandeza', ['Eh', 'Eh/Em', 'vh'])
def test_figura_comparacao_desenha_faixa_e_leitura(resultado_concreto, grandeza):
    fig = figura_comparacao(resultado_concreto, grandeza, fi_leitura=0.30)
    ax = fig.axes[0]
    assert ax.get_xlabel() == 'fração volumétrica de inclusão fi'
    assert len(ax.collections) == 1
    rotulos = [t.get_text() for t in fig.legends[0].get_texts()]
    assert rotulos == ['Faixa Voigt–Reuss', 'Mori-Tanaka', 'Self-Consistent', 'GSC']
    assert any(t.get_text() == 'fi 0,30' for t in ax.texts)


def test_figura_comparacao_tracejada_fora_da_validade():
    r = calcular(EntradaComposito(modelos=('Dilute Suspension',)))
    linhas = figura_comparacao(r, 'Eh').axes[0].get_lines()
    assert [l.get_linestyle() for l in linhas] == ['-', '--']
    assert linhas[0].get_xdata()[-1] == pytest.approx(0.10)


def test_modelos_individuais_na_mesma_escala(resultado_concreto):
    figs = [figura_modelo_individual(resultado_concreto, n) for n in resultado_concreto.curvas]
    escalas = {f.axes[0].get_ylim() for f in figs}
    assert escalas == {limites_y(resultado_concreto, 'Eh')}


def test_dominio_nao_importa_a_interface():
    raiz = pathlib.Path(__file__).resolve().parents[1] / 'src' / 'hoop'
    infratores = [str(p.relative_to(raiz)) for p in raiz.rglob('*.py')
                  if 'ui' not in p.relative_to(raiz).parts
                  and re.search(r'^\s*(from|import)\s+hoop\.ui\b', p.read_text('utf-8'), re.M)]
    assert infratores == []


def test_cada_grandeza_sabe_extrair_e_ler_a_matriz():
    entrada = EntradaComposito()
    r = ResultadoMecanico(Eh=40_000, vh=0.25, Em=entrada.Em)
    assert {g: info.extrair(r) for g, info in GRANDEZAS.items()} == pytest.approx(
        {'Eh': 40_000, 'Eh/Em': 40_000 / 30_000, 'vh': 0.25})
    assert {g: info.valor_na_matriz(entrada) for g, info in GRANDEZAS.items()} == {
        'Eh': 30_000, 'Eh/Em': 1.0, 'vh': 0.20}
    assert len({info.sufixo_arquivo for info in GRANDEZAS.values()}) == len(GRANDEZAS)


def test_referencia_prefere_modelos_que_nao_sao_limites(resultado_concreto):
    assert escolher_referencia(resultado_concreto) == 'Mori-Tanaka'
    assert escolher_referencia(resultado_concreto, 'GSC') == 'GSC'
    so_limites = calcular(replace(EntradaComposito(), modelos=('Voigt', 'Reuss', 'GSC')))
    assert escolher_referencia(so_limites) == 'GSC'
    assert abreviar('Mori-Tanaka') == 'MT' and abreviar('GSC') == 'GSC'
