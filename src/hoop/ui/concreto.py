"""Concreto multiescala na interface, sem Streamlit: entrada, validação, prévia e cálculo.

A entrada usa MPa e frações de 0 a 1 (a tela mostra %). ``calcular_concreto_ui``
roda ``hoop.homogenizacao.multiescala.calcular_concreto`` para cada modelo
escolhido; um modelo que falha vira uma ``FalhaConcreto`` e os demais seguem.
O núcleo não depende de unidade, então os módulos entram em MPa direto.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Callable, Dict, Mapping, Optional, Tuple

from hoop.homogenizacao.multiescala import (POISSON_POROS, TOLERANCIA_SOMA, Constituinte,
                                            FasesConcreto, ResultadoMultiescala,
                                            calcular_concreto)
from hoop.materiais.fases import FaseMecanica
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.multiplasfases import MultiplasFases
from hoop.micmodelos.quatrofases import QuatroFases
from hoop.ui.calculo import ERROS_DE_MODELO, LIMITES, MODELOS
from hoop.ui.formatacao import formatar_decimal, formatar_numero, formatar_percentual

MPA_POR_GPA = 1000.0


@dataclass(frozen=True)
class InfoFaseConcreto:
    """Nome exibido, papel e ícone de uma fase do concreto (chave = atributo da entrada)."""
    chave: str
    nome: str
    papel: str
    icone: str


FASES_CONCRETO: Dict[str, InfoFaseConcreto] = {
    f.chave: f for f in (
        InfoFaseConcreto('pasta', 'Pasta de cimento', 'matriz da argamassa', ':material/grid_on:'),
        InfoFaseConcreto('agregado_miudo', 'Agregado miúdo', 'areia', ':material/grain:'),
        InfoFaseConcreto('zti_miudo', 'ZTI do miúdo', 'ZTI-2, envolve o miúdo',
                         ':material/blur_circular:'),
        InfoFaseConcreto('agregado_graudo', 'Agregado graúdo', 'brita',
                         ':material/bubble_chart:'),
        InfoFaseConcreto('zti_graudo', 'ZTI do graúdo', 'ZTI-1, envolve o graúdo',
                         ':material/blur_circular:'),
    )
}
"""Na ordem dos cartões: nível 1 (pasta, miúdo, ZTI-2) e nível 2 (graúdo, ZTI-1)."""

ZTIS: Tuple[str, str] = ('zti_miudo', 'zti_graudo')
AGREGADO_DA_ZTI: Dict[str, str] = {'zti_miudo': 'agregado_miudo', 'zti_graudo': 'agregado_graudo'}

COM_ZTI, SEM_ZTI = 'com_zti', 'sem_zti'
CONSTRUCOES: Dict[str, str] = {COM_ZTI: 'Com ZTI', SEM_ZTI: 'Sem ZTI'}
CONSTRUCOES_MINUSCULAS: Dict[str, str] = {COM_ZTI: 'com ZTI', SEM_ZTI: 'sem ZTI'}


@dataclass(frozen=True)
class InfoModeloTresFases:
    """Modelo de três fases (inclusão revestida) para a construção com ZTI."""
    nome: str
    classe: Callable
    descricao: str


MODELOS_ZTI: Dict[str, InfoModeloTresFases] = {
    m.nome: m for m in (
        InfoModeloTresFases('Quatro fases', QuatroFases,
                            'Li et al. (1999): GSC no agregado com a ZTI e depois na matriz.'),
        InfoModeloTresFases('Múltiplas fases', MultiplasFases,
                            'Shi et al. (2020), forma do código do autor. ZTI até o volume '
                            'do agregado.'),
    )
}
MODELOS_SEM_ZTI: Tuple[str, ...] = tuple(MODELOS)
"""Sem ZTI, os modelos de duas fases do modo atual (chaves de ``calculo.MODELOS``)."""

MODELOS_ZTI_PADRAO: Tuple[str, ...] = ('Quatro fases',)
DESTAQUE_PADRAO: Tuple[str, ...] = ('Quatro fases', 'Mori-Tanaka')
"""Modelo destacado por padrão na Análise, no PDF e na barra lateral, se calculado."""
MODELOS_SEM_ZTI_PADRAO: Tuple[str, ...] = ('Mori-Tanaka', 'Self-Consistent', 'GSC')

POROS_MT, POROS_MESMO = 'mori_tanaka', 'mesmo'
MODELOS_POROS: Dict[str, str] = {POROS_MT: 'Mori-Tanaka (como na tese)',
                                 POROS_MESMO: 'O mesmo de cada série'}

NIVEIS: Tuple[str, ...] = ('Argamassa', 'Concreto', 'Concreto com poros')
ROTULOS_NIVEL: Tuple[str, ...] = ('1 · Argamassa', '2 · Concreto', '3 · Com poros')


@dataclass(frozen=True)
class PropriedadesFase:
    """E [MPa], ν e fração no concreto (0 a 1) de uma fase sólida."""
    E: float
    v: float
    fracao: float


@dataclass(frozen=True)
class EntradaConcreto:
    """Tudo o que a etapa Dados define no modo multiescala. Padrão: Li et al. (2019).

    ``poros`` é a fração de poros em relação aos sólidos (0 a 1);
    ``E_experimental`` em MPa ou None. As listas de modelos das duas
    construções ficam guardadas para a troca Com/Sem ZTI não perder a escolha.
    """
    pasta: PropriedadesFase = PropriedadesFase(21_340.0, 0.25, 0.154)
    agregado_miudo: PropriedadesFase = PropriedadesFase(77_600.0, 0.15, 0.269)
    zti_miudo: PropriedadesFase = PropriedadesFase(12_700.0, 0.25, 0.151)
    agregado_graudo: PropriedadesFase = PropriedadesFase(51_310.0, 0.15, 0.403)
    zti_graudo: PropriedadesFase = PropriedadesFase(10_170.0, 0.30, 0.023)
    poros: float = 0.0242
    E_experimental: Optional[float] = 34_500.0
    construcao: str = COM_ZTI
    modelos_zti: Tuple[str, ...] = field(default=MODELOS_ZTI_PADRAO)
    modelos_sem_zti: Tuple[str, ...] = field(default=MODELOS_SEM_ZTI_PADRAO)
    modelo_poros: str = POROS_MT

    @property
    def com_zti(self) -> bool:
        return self.construcao == COM_ZTI

    @property
    def modelos(self) -> Tuple[str, ...]:
        """Modelos da construção escolhida."""
        return self.modelos_zti if self.com_zti else self.modelos_sem_zti

    def fase(self, chave: str) -> PropriedadesFase:
        return getattr(self, chave)


def eh_padrao_da_tese(entrada: EntradaConcreto) -> bool:
    """True se fases, poros e E experimental são os de Li et al. (2019)."""
    padrao = EntradaConcreto()
    campos = (*FASES_CONCRETO, 'poros', 'E_experimental')
    return all(getattr(entrada, c) == getattr(padrao, c) for c in campos)


def restaurar_tese(entrada: EntradaConcreto) -> EntradaConcreto:
    """Volta fases, poros e E experimental aos valores da tese; mantém construção e modelos."""
    padrao = EntradaConcreto()
    return replace(entrada, **{c: getattr(padrao, c)
                               for c in (*FASES_CONCRETO, 'poros', 'E_experimental')})


# --- Validação --------------------------------------------------------------

def _erro_modulo(E: float) -> Optional[str]:
    return None if math.isfinite(E) and E > 0 else 'Informe um módulo maior que zero.'


def _erro_poisson(v: float) -> Optional[str]:
    if math.isfinite(v) and 0 <= v < 0.5:
        return None
    if math.isfinite(v) and v >= 0.5:
        return ('Use um valor menor que 0,5. Com 0,5 o material é incompressível '
                'e os tensores não podem ser invertidos.')
    return 'ν precisa estar entre 0 e 0,5.'


def _erro_fracao(chave: str, fracao: float) -> Optional[str]:
    if not (math.isfinite(fracao) and 0 <= fracao <= 1):
        return 'Use uma fração entre 0 e 100%.'
    if chave == 'pasta' and fracao == 0:
        return 'A pasta é a matriz da argamassa: use uma fração maior que zero.'
    return None


def soma_fracoes(entrada: EntradaConcreto) -> float:
    """Soma das frações sólidas (as cinco fases; os poros ficam de fora)."""
    return sum(entrada.fase(c).fracao for c in FASES_CONCRETO)


def validar_concreto(entrada: EntradaConcreto) -> Dict[str, str]:
    """Erros por campo ('pasta.E', 'poros', 'soma', 'modelos'...); vazio se a entrada é válida."""
    erros: Dict[str, Optional[str]] = {}
    for chave in FASES_CONCRETO:
        fase = entrada.fase(chave)
        erros[f'{chave}.E'] = _erro_modulo(fase.E)
        erros[f'{chave}.v'] = _erro_poisson(fase.v)
        erros[f'{chave}.fracao'] = _erro_fracao(chave, fase.fracao)
    soma = soma_fracoes(entrada)
    if math.isfinite(soma) and abs(soma - 1) > TOLERANCIA_SOMA:
        erros['soma'] = (f'As frações sólidas somam {formatar_percentual(soma, 2)}. '
                         'Ajuste para 100% (os poros ficam de fora dessa soma).')
    if not (math.isfinite(entrada.poros) and 0 <= entrada.poros < 1):
        erros['poros'] = 'Use uma fração de poros de 0 até menos de 100%.'
    if entrada.com_zti:
        for zti, agregado in AGREGADO_DA_ZTI.items():
            if entrada.fase(zti).fracao > 0 and entrada.fase(agregado).fracao == 0 \
                    and not erros[f'{agregado}.fracao']:
                nome_zti = FASES_CONCRETO[zti].nome
                erros[f'{agregado}.fracao'] = (
                    f'A {nome_zti} envolve o {FASES_CONCRETO[agregado].nome.lower()}: '
                    'informe uma fração maior que zero ou zere a ZTI.')
    if entrada.E_experimental is not None and _erro_modulo(entrada.E_experimental):
        erros['E_experimental'] = ('Informe um módulo maior que zero ou deixe o campo vazio '
                                   'para não comparar.')
    catalogo = MODELOS_ZTI if entrada.com_zti else MODELOS
    if not entrada.modelos:
        erros['modelos'] = 'Selecione ao menos um modelo para comparar.'
    elif any(m not in catalogo for m in entrada.modelos):
        erros['modelos'] = 'Há um modelo desconhecido na seleção.'
    if entrada.construcao not in CONSTRUCOES:
        erros['construcao'] = 'Escolha Com ZTI ou Sem ZTI.'
    return {campo: msg for campo, msg in erros.items() if msg}


# --- Prévia dos níveis ------------------------------------------------------

@dataclass(frozen=True)
class FaseNoNivel:
    """Uma fase dentro de um nível: chave de cor (``tema.CORES_FASE``), rótulo e fração."""
    chave: str
    rotulo: str
    fracao: float


@dataclass(frozen=True)
class PreviaNivel:
    """Um nível da prévia: número, nome e fases (matriz primeiro) com as frações no nível."""
    numero: int
    nome: str
    fases: Tuple[FaseNoNivel, ...]


def _normalizar(itens: Tuple[Tuple[str, str, float], ...]) -> Tuple[FaseNoNivel, ...]:
    total = sum(f for _, _, f in itens)
    return tuple(FaseNoNivel(c, r, f / total if total > 0 else 0.0) for c, r, f in itens)


def previa_niveis(entrada: EntradaConcreto) -> Tuple[PreviaNivel, ...]:
    """Frações corrigidas de cada nível, com a mesma regra de ``calcular_concreto``.

    Nível 1: pasta + miúdo (+ ZTI-2); nível 2: argamassa + graúdo (+ ZTI-1);
    nível 3, só com poros: concreto + poros, com poros / (sólidos considerados + poros).
    """
    f = entrada.fase
    nivel1 = [('pasta', 'Pasta de cimento', f('pasta').fracao),
              ('agregado_miudo', 'Agregado miúdo', f('agregado_miudo').fracao)]
    if entrada.com_zti:
        nivel1.append(('zti_miudo', 'ZTI-2', f('zti_miudo').fracao))
    argamassa = sum(x for _, _, x in nivel1)
    nivel2 = [('argamassa', 'Argamassa', argamassa),
              ('agregado_graudo', 'Agregado graúdo', f('agregado_graudo').fracao)]
    if entrada.com_zti:
        nivel2.append(('zti_graudo', 'ZTI-1', f('zti_graudo').fracao))
    niveis = [PreviaNivel(1, NIVEIS[0], _normalizar(tuple(nivel1))),
              PreviaNivel(2, NIVEIS[1], _normalizar(tuple(nivel2)))]
    if entrada.poros > 0:
        solidos = sum(x for _, _, x in nivel2)
        niveis.append(PreviaNivel(3, NIVEIS[2], _normalizar(
            (('concreto', 'Concreto', solidos), ('poros', 'Poros', entrada.poros)))))
    return tuple(niveis)


# --- Cálculo ----------------------------------------------------------------

@dataclass(frozen=True)
class FalhaConcreto:
    """Um modelo parou: ``nivel`` (1 a 3) quando se sabe onde, e a mensagem do domínio."""
    mensagem: str
    nivel: Optional[int] = None


@dataclass(frozen=True)
class SerieConcreto:
    """Resultado de um modelo: os níveis calculados e, se parou antes do fim, a falha.

    ``fora_da_validade`` lista os níveis (1 a 3) em que o modelo foi usado com
    fração de inclusão acima da sua validade (``InfoModelo.fi_validade``).
    """
    nome: str
    multiescala: Optional[ResultadoMultiescala]
    falha: Optional[FalhaConcreto] = None
    fora_da_validade: Tuple[int, ...] = ()

    @property
    def completa(self) -> bool:
        return self.multiescala is not None and self.falha is None

    @property
    def niveis(self):
        return self.multiescala.niveis if self.multiescala else ()

    @property
    def Eh(self) -> Optional[float]:
        """E do concreto (último nível), ou None se o modelo não chegou ao fim."""
        return self.multiescala.Eh if self.completa else None

    @property
    def erro_relativo(self) -> Optional[float]:
        return self.multiescala.erro_relativo if self.completa else None


@dataclass(frozen=True)
class ResultadoConcreto:
    """Resultado de ``calcular_concreto_ui``: a entrada usada e uma série por modelo."""
    entrada: EntradaConcreto
    series: Mapping[str, SerieConcreto]

    @property
    def calculados(self) -> Tuple[str, ...]:
        """Modelos que chegaram ao último nível."""
        return tuple(n for n, s in self.series.items() if s.completa)

    @property
    def falhas(self) -> Dict[str, FalhaConcreto]:
        return {n: s.falha for n, s in self.series.items() if s.falha}

    @property
    def numero_niveis(self) -> int:
        return 3 if self.entrada.poros > 0 else 2


def fases_concreto(entrada: EntradaConcreto) -> FasesConcreto:
    """``FasesConcreto`` do núcleo com os módulos em MPa (as ZTIs sempre vão juntas)."""
    def constituinte(chave: str) -> Constituinte:
        f = entrada.fase(chave)
        return Constituinte(FaseMecanica(f.E, f.v), f.fracao)
    return FasesConcreto(**{c: constituinte(c) for c in FASES_CONCRETO},
                         poros=entrada.poros, E_experimental=entrada.E_experimental)


def _modelos(entrada: EntradaConcreto, nome: str):
    """(modelo dos níveis sólidos, modelo dos poros) para a série ``nome``."""
    if entrada.com_zti:
        return MODELOS_ZTI[nome].classe(), MoriTanaka()
    modelo = MODELOS[nome].classe()
    poros = MODELOS[nome].classe() if entrada.modelo_poros == POROS_MESMO else MoriTanaka()
    return modelo, poros


def fi_validade(entrada: EntradaConcreto, nome: str) -> Optional[float]:
    """Fração máxima de validade do modelo ``nome`` (só modelos de duas fases a têm)."""
    return None if entrada.com_zti else MODELOS[nome].fi_validade


def niveis_fora_da_validade(entrada: EntradaConcreto, nome: str,
                            multiescala: ResultadoMultiescala) -> Tuple[int, ...]:
    """Níveis em que ``nome`` homogeneíza uma fração de inclusão acima da sua validade."""
    limite = fi_validade(entrada, nome)
    if limite is None:
        return ()
    usa_o_modelo = (True, True, entrada.modelo_poros == POROS_MESMO)
    return tuple(i for i, (nivel, usa) in enumerate(zip(multiescala.niveis, usa_o_modelo), 1)
                 if usa and nivel.fracoes[1] > limite + 1e-12)


def _serie(entrada: EntradaConcreto, nome: str, multiescala: ResultadoMultiescala,
           falha: Optional[FalhaConcreto] = None) -> SerieConcreto:
    return SerieConcreto(nome, multiescala, falha,
                         niveis_fora_da_validade(entrada, nome, multiescala))


def calcular_serie(entrada: EntradaConcreto, nome: str) -> SerieConcreto:
    """Calcula um modelo; se falhar com poros, refaz sem eles para guardar os níveis 1 e 2.

    Um E não finito ou não positivo chega como ValueError do núcleo e vira a falha.
    """
    fases = fases_concreto(entrada)
    modelo, modelo_poros = _modelos(entrada, nome)
    try:
        return _serie(entrada, nome,
                      calcular_concreto(fases, modelo, entrada.com_zti, modelo_poros))
    except ERROS_DE_MODELO as erro:
        mensagem = str(erro)
    if fases.poros > 0:
        try:
            parcial = calcular_concreto(replace(fases, poros=0.0), modelo, entrada.com_zti)
            return _serie(entrada, nome, parcial, FalhaConcreto(mensagem, nivel=3))
        except ERROS_DE_MODELO:
            pass
    return SerieConcreto(nome, None, FalhaConcreto(mensagem))


def calcular_concreto_ui(entrada: EntradaConcreto,
                         ao_progredir: Optional[Callable[[str, int, int], None]] = None
                         ) -> ResultadoConcreto:
    """Calcula todos os modelos da construção escolhida, na ordem do catálogo."""
    nomes = tuple(entrada.modelos)
    series = {}
    for i, nome in enumerate(nomes):
        if ao_progredir:
            ao_progredir(nome, i, len(nomes))
        series[nome] = calcular_serie(entrada, nome)
    return ResultadoConcreto(entrada, series)


# --- Textos -----------------------------------------------------------------

def resumo_concreto(entrada: EntradaConcreto) -> str:
    """Resumo curto para a barra lateral: "Concreto · com ZTI · 1 modelo"."""
    n = len(entrada.modelos)
    modelos = f'{n} modelo' if n == 1 else f'{n} modelos'
    return f'Concreto · {CONSTRUCOES_MINUSCULAS[entrada.construcao]} · {modelos}'


def escolher_destaque(resultado: ResultadoConcreto, escolhido: Optional[str] = None
                      ) -> Optional[str]:
    """Modelo destacado: o escolhido, senão Quatro fases ou Mori-Tanaka, senão o primeiro
    que não é limite; só cai em Voigt ou Reuss se nenhum outro chegou ao fim."""
    calculados = resultado.calculados
    nao_limites = [n for n in calculados if n not in LIMITES]
    candidatos = [escolhido, *DESTAQUE_PADRAO, *nao_limites, *calculados]
    return next((n for n in candidatos if n in calculados), None)


def aviso_validade(resultado: ResultadoConcreto, nome: str) -> Optional[str]:
    """Texto da ressalva quando ``nome`` foi usado acima da sua validade; None se não foi."""
    serie = resultado.series[nome]
    if not serie.fora_da_validade:
        return None
    entrada = resultado.entrada
    fracoes = [serie.niveis[i - 1].fracoes[1] for i in serie.fora_da_validade]
    niveis = ' e '.join(str(i) for i in serie.fora_da_validade)
    usadas = ' e '.join(formatar_percentual(f) for f in fracoes)
    sujeito = f'os níveis {niveis} usam' if len(fracoes) > 1 else f'o nível {niveis} usa'
    return (f'{nome} vale até fi ≈ {formatar_decimal(fi_validade(entrada, nome))}, mas '
            f'{sujeito} inclusão de {usadas}. Leia esses valores como estimativa fora da '
            'validade do modelo ou compare com Mori-Tanaka.')


def resumo_analise_concreto(resultado: ResultadoConcreto, destaque: Optional[str] = None) -> str:
    """Resumo da Análise: "Quatro fases · Ec 34 645 MPa" (do modelo destacado)."""
    nome = escolher_destaque(resultado, destaque)
    if nome is None:
        return 'Nenhum modelo calculado'
    return f'{nome} · Ec {formatar_numero(resultado.series[nome].Eh)} MPa'


def poisson_poros_texto() -> str:
    return formatar_numero(POISSON_POROS, 1)
