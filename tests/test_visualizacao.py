import matplotlib.pyplot as plt
import pytest
from matplotlib.figure import Figure

from hoop.exemplos import criar_analise, MATERIAIS
from hoop.desenho.desenho_cond import DesenhoCondutividade
from hoop.desenho.desenho_mec import DesenhoMecanico
from hoop.desenho.estilos.estilo_registry import EstiloRegistry
from hoop.homogenizacao.composito import Composito
from hoop.homogenizacao.homogenizacao import Homogenizacao
from hoop.homogenizacao.varredura import Curva, varrer
from hoop.materiais.condutividade import Condutividade
from hoop.materiais.fases import FaseCondutividade, FaseMecanica
from hoop.mecanico.mecanico import Mecanico
from hoop.micmodelos.gsc import GSC
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.reuss import Reuss
from hoop.micmodelos.voigt import Voigt
from hoop.relatorio.relatorio import gerar_relatorio

CONCRETO = MATERIAIS['concreto']


@pytest.fixture(autouse=True)
def fechar_figuras():
    yield
    plt.close('all')


@pytest.fixture
def show_proibido(monkeypatch):
    def falhar(*a, **k):
        raise AssertionError('plt.show() não deve ser chamado pelo pacote desenho')
    monkeypatch.setattr(plt, 'show', falhar)


def analise_condutividade(km=1.0, ki=10.0):
    h = Homogenizacao()
    h.tipo = 'global'
    h.analise_tipo = 'condutividade'
    h.geo = 'esfera'
    h.set_analise()
    for k in (km, ki):
        c = Condutividade()
        c.k11 = c.k22 = c.k33 = k
        h.matH.append(c)
    return h


# ── varrer(): domínio puro ──────────────────────────────────────────────────

def composito_concreto(fi=0.0):
    return Composito(FaseMecanica(CONCRETO['Em'], CONCRETO['vm']),
                     FaseMecanica(CONCRETO['Ei'], CONCRETO['vi']), fi=fi)


def test_varrer_devolve_curva_com_101_pontos_de_0_a_1():
    curva = varrer(composito_concreto(), Voigt(), lambda r: r.Eh)

    assert isinstance(curva, Curva)
    assert curva.nome == 'Voigt'
    assert len(curva.xs) == len(curva.ys) == 101
    assert curva.xs[0] == 0.0 and curva.xs[-1] == 1.0
    assert curva.ys[0] == pytest.approx(CONCRETO['Em'], rel=1e-9)
    assert curva.ys[-1] == pytest.approx(CONCRETO['Ei'], rel=1e-9)


def test_varrer_usa_os_mesmos_pontos_do_laco_original():
    curva = varrer(composito_concreto(), Reuss(), lambda r: r.Eh)
    assert curva.xs == [i / 100 for i in range(101)]


def test_varrer_respeita_fi_max_e_passos():
    curva = varrer(composito_concreto(), Voigt(), lambda r: r.Eh, fi_max=0.5, passos=10)
    assert len(curva.xs) == 11
    assert curva.xs[-1] == pytest.approx(0.5)


@pytest.mark.parametrize('kwargs', [dict(passos=0), dict(fi_max=0.0), dict(fi_max=1.5)])
def test_varrer_rejeita_parametros_invalidos(kwargs):
    with pytest.raises(ValueError):
        varrer(composito_concreto(), Voigt(), lambda r: r.Eh, **kwargs)


def test_varrer_nao_altera_composito_nem_modelo():
    base = composito_concreto(fi=0.3)
    modelo = MoriTanaka()
    estado_antes = dict(vars(modelo))

    curva = varrer(base, modelo, lambda r: r.Eh)

    assert base.fi == 0.3
    assert vars(modelo) == estado_antes
    assert curva.ys[30] == MoriTanaka().homogeneizar(base).Eh


def test_varrer_de_condutividade_usa_o_metodo_de_condutividade():
    base = Composito(FaseCondutividade.isotropica(1.0), FaseCondutividade.isotropica(10.0), fi=0)
    curva = varrer(base, Voigt(), lambda r: r.K11, passos=10)
    assert curva.ys[0] == pytest.approx(1.0) and curva.ys[-1] == pytest.approx(10.0)


def test_varrer_falha_com_modelo_que_nao_suporta_a_analise():
    from hoop.micmodelos.micmodelos import Micmodelos
    from hoop.micmodelos.protocolos import ModeloMecanico

    class SoMecanico(Micmodelos, ModeloMecanico):
        def homogeneizar(self, composito):
            raise AssertionError('não deveria ser chamado')

    base = Composito(FaseCondutividade.isotropica(1.0), FaseCondutividade.isotropica(10.0), fi=0)
    with pytest.raises(ValueError, match='não suportado'):
        varrer(base, SoMecanico(), lambda r: r.K11)


def test_varrer_nao_importa_matplotlib():
    import ast
    import inspect
    import hoop.homogenizacao.varredura as mod
    arvore = ast.parse(inspect.getsource(mod))
    importados = {n.names[0].name for n in ast.walk(arvore) if isinstance(n, ast.Import)}
    importados |= {n.module for n in ast.walk(arvore) if isinstance(n, ast.ImportFrom)}
    assert not any('matplotlib' in m or 'seaborn' in m for m in importados)


# ── estilos: extração separada da configuração de eixo ─────────────────────

@pytest.mark.parametrize('estilo, esperado', [
    ('fixar_fracao', lambda m: m.Eh),
    ('normalizar', lambda m: m.Eh / m.Em),
    ('poisson', lambda m: m.vh),
])
def test_estilo_extrai_valor_sem_calcular(estilo, esperado):
    h = criar_analise(**CONCRETO)
    h.modH = MoriTanaka()
    h.analH.fi = 0.4
    h.calc()
    fi_antes = h.analH.fi

    assert EstiloRegistry.obter(estilo).extrair(h.modH) == esperado(h.modH)
    assert h.analH.fi == fi_antes


# ── DesenhoMecanico: só desenha e devolve Figure ───────────────────────────

def test_desenha_devolve_figure_sem_chamar_show(show_proibido):
    h = criar_analise(**CONCRETO)
    d = DesenhoMecanico(estilo='normalizar')

    fig = d.desenha(h, modelo=MoriTanaka())

    assert isinstance(fig, Figure)
    linha = fig.axes[0].get_lines()[0]
    assert list(linha.get_xdata()) == d.curvas[0].xs
    assert fig.axes[0].get_ylabel() == 'Eh / Em'


def test_juntar_grafs_devolve_figure_sem_chamar_show(show_proibido):
    h = criar_analise(**CONCRETO)
    d = DesenhoMecanico(estilo='poisson')
    d.desenha(h, modelo=GSC())
    d.desenha(h, modelo=Voigt())

    fig = d.juntar_grafs(limites_y=(0.1, 0.4))

    assert isinstance(fig, Figure)
    assert [l.get_label() for l in fig.axes[0].get_lines()] == ['GSC', 'Voigt']
    assert fig.axes[0].get_ylim() == (0.1, 0.4)


def test_desenho_nao_altera_rcparams_globais():
    antes = dict(plt.rcParams)
    d = DesenhoMecanico(estilo='fixar_fracao')
    d.desenha(criar_analise(**CONCRETO), modelo=Voigt())
    d.juntar_grafs()
    assert dict(plt.rcParams) == antes


def test_graphs_mantem_compatibilidade_com_curvas():
    d = DesenhoMecanico(estilo='fixar_fracao')
    d.desenha(criar_analise(**CONCRETO), modelo=Voigt())
    xs, ys, nome = d.graphs[0]
    assert (xs, ys, nome) == (d.curvas[0].xs, d.curvas[0].ys, 'Voigt')


def test_desenha_respeita_fi_maximo_da_analise():
    h = criar_analise(**CONCRETO, fi=0.5)
    d = DesenhoMecanico(estilo='fixar_fracao')
    d.desenha(h, modelo=Voigt())
    xs = d.curvas[0].xs
    assert len(xs) == 51 and xs[-1] == pytest.approx(0.5)


def test_estilo_vazio_usa_fixar_fracao_e_desconhecido_falha_cedo():
    assert DesenhoMecanico(estilo='').estilo == 'fixar_fracao'
    with pytest.raises(ValueError, match='não registrado'):
        DesenhoMecanico(estilo='inexistente')


def test_desenho_mecanico_recusa_analise_de_condutividade():
    d = DesenhoMecanico(estilo='fixar_fracao')
    with pytest.raises(ValueError, match="exige análise 'mecanica'"):
        d.desenha(analise_condutividade(), modelo=Voigt())


# ── Condutividade: mesmo desenho, outro estilo ─────────────────────────────

@pytest.mark.parametrize('Modelo', [Voigt, MoriTanaka])
def test_desenho_condutividade_vai_da_matriz_a_inclusao(Modelo):
    d = DesenhoCondutividade(direcao='k22')
    fig = d.desenha(analise_condutividade(km=1.0, ki=10.0), modelo=Modelo())

    curva = d.curvas[0]
    assert isinstance(fig, Figure)
    assert len(curva.xs) == 101
    assert curva.ys[0] == pytest.approx(1.0)
    assert curva.ys[-1] == pytest.approx(10.0)
    assert fig.axes[0].get_ylabel() == 'K22'


def test_desenho_condutividade_le_o_valor_do_ponto_atual():
    """O desenho antigo lia K antes de calc() e ficava um ponto atrasado."""
    d = DesenhoCondutividade()
    d.desenha(analise_condutividade(km=1.0, ki=10.0), modelo=Voigt())
    assert d.curvas[0].ys[50] == pytest.approx(5.5)


def test_desenho_condutividade_recusa_direcao_invalida():
    with pytest.raises(ValueError):
        DesenhoCondutividade(direcao='K44')


# ── Homogenizacao: 2 fases, sem matplotlib ─────────────────────────────────

def test_tres_fases_gera_erro_claro():
    h = criar_analise(**CONCRETO)
    terceira = Mecanico()
    terceira.E, terceira.v = 1000, 0.3
    h.matH.append(terceira)
    h.modH = Voigt()
    with pytest.raises(ValueError, match='2 fases'):
        h.calc()


def test_tipo_de_homogeneizacao_desconhecido_gera_erro():
    h = criar_analise(**CONCRETO)
    h.tipo = 'local'
    h.modH = Voigt()
    with pytest.raises(ValueError, match="tipo = 'global'"):
        h.calc()


def test_homogenizacao_nao_depende_de_matplotlib():
    import hoop.homogenizacao.homogenizacao as mod
    assert not hasattr(mod, 'plt')
    assert not hasattr(mod.Homogenizacao, 'showFrac')


# ── Relatório PDF ──────────────────────────────────────────────────────────

def test_relatorio_pdf_e_gerado(tmp_path):
    h = criar_analise(**CONCRETO)
    d = DesenhoMecanico(estilo='normalizar')
    d.desenha(h, modelo=GSC())
    d.desenha(h, modelo=MoriTanaka())

    destino = tmp_path / 'relatorio.pdf'
    gerar_relatorio(h, d, filename=str(destino))

    conteudo = destino.read_bytes()
    assert conteudo.startswith(b'%PDF')
    assert len(conteudo) > 10_000


def test_relatorio_sem_curvas_gera_erro(tmp_path):
    with pytest.raises(ValueError, match='Nenhum modelo'):
        gerar_relatorio(criar_analise(**CONCRETO), DesenhoMecanico(),
                        filename=str(tmp_path / 'x.pdf'))
