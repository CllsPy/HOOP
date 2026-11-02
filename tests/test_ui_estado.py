from dataclasses import replace

import matplotlib.pyplot as plt
import numpy as np
import pytest

from cases._setup import MATERIAIS
from ui import calculo
from ui.calculo import MODELOS, MODELOS_PADRAO, InfoModelo, calcular, fracoes, valor_em
from ui.estado import (PERSONALIZADO, PRESETS, EntradaComposito, aplicar_preset,
                       formatar_decimal, formatar_numero, formatar_percentual,
                       interpretar_numero, preset_correspondente, resumo_entrada, validar)
from ui.graficos import figura_comparacao, figura_modelo_individual, limites_y

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
    def __init__(self):
        self.tipo = 'Falso'
        self.Em = 30_000

    def calc(self, objH):
        fi = objH.analH.fi
        if fi > 0.855:
            raise ValueError('Sem raiz real.')
        self.Eh, self.vh = 30_000 * (1 + fi), 0.2


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
