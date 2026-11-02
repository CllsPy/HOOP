"""Homogeneização multiescala do concreto (estudo de caso 3.1 da tese).

O concreto é montado em níveis, cada um homogeneizando o resultado do nível
anterior com novas fases:

* com ZTI: nível 1 = pasta + agregado miúdo revestido pela ZTI-2 (modelo de
  três fases); nível 2 = argamassa + agregado graúdo revestido pela ZTI-1;
  nível 3 = concreto + poros;
* sem ZTI: nível 1 = pasta + agregado miúdo; nível 2 = argamassa + agregado
  graúdo; nível 3 = concreto + poros (modelos de duas fases).

As frações de cada nível são as frações no concreto divididas pela soma das
frações das fases daquele nível (Tabelas 4 e 7 da tese). Os poros são dados
em relação aos sólidos (2,42% sobre 100% de sólidos) e entram no último
nível com fração poros / (sólidos considerados + poros).
"""
import math
from dataclasses import dataclass
from numbers import Real
from typing import Optional, Tuple

from hoop.homogenizacao.composito import Composito, CompositoRevestido
from hoop.materiais.fases import FaseMecanica
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.protocolos import ModeloMecanico, ModeloTresFases
from hoop.resultados.resultados import ResultadoMecanico

TOLERANCIA_SOMA = 1e-3   # folga na soma das frações sólidas (0,1 ponto percentual)
POISSON_POROS = 0.2


def _exigir_fracao(nome: str, valor, aberta_em_1: bool = False) -> None:
    if isinstance(valor, bool) or not isinstance(valor, Real) or not math.isfinite(valor) \
            or valor < 0 or valor > 1 or (aberta_em_1 and valor == 1):
        faixa = '[0, 1)' if aberta_em_1 else '[0, 1]'
        raise ValueError(f"{nome} deve estar em {faixa} (fração, não %). Recebido: {valor!r}.")


@dataclass(frozen=True)
class Constituinte:
    """Uma fase do concreto e a sua fração volumétrica no concreto (0 a 1)."""
    fase: FaseMecanica
    fracao: float

    def __post_init__(self):
        if not isinstance(self.fase, FaseMecanica) or self.fase.vazio:
            raise ValueError(
                "fase deve ser uma FaseMecanica sólida (E > 0). Os poros entram pelo campo "
                "'poros' de FasesConcreto."
            )
        _exigir_fracao('fracao', self.fracao)


@dataclass(frozen=True)
class FasesConcreto:
    """Fases do concreto e frações no concreto (0 a 1).

    As ZTIs são opcionais, mas vêm juntas: ``zti_miudo`` (ZTI-2, em torno do
    agregado miúdo) e ``zti_graudo`` (ZTI-1, em torno do graúdo). A soma das
    frações sólidas informadas deve ser 1. ``poros`` é a fração de poros em
    relação aos sólidos; ``E_experimental`` (mesma unidade de E), se dado,
    permite calcular o erro relativo.
    """
    pasta: Constituinte
    agregado_miudo: Constituinte
    agregado_graudo: Constituinte
    zti_miudo: Optional[Constituinte] = None
    zti_graudo: Optional[Constituinte] = None
    poros: float = 0.0
    E_experimental: Optional[float] = None

    def __post_init__(self):
        for nome in ('pasta', 'agregado_miudo', 'agregado_graudo', 'zti_miudo', 'zti_graudo'):
            valor = getattr(self, nome)
            if valor is None and nome.startswith('zti'):
                continue
            if not isinstance(valor, Constituinte):
                raise ValueError(
                    f"{nome} deve ser um Constituinte(fase, fracao). "
                    f"Recebido: {type(valor).__name__}."
                )
        if self.pasta.fracao == 0:
            raise ValueError(
                "A pasta é a matriz da argamassa: use uma fração de pasta maior que zero."
            )
        if (self.zti_miudo is None) != (self.zti_graudo is None):
            raise ValueError(
                "Informe as duas ZTIs (zti_miudo e zti_graudo) ou nenhuma delas."
            )
        _exigir_fracao('poros', self.poros, aberta_em_1=True)
        if self.E_experimental is not None and (
                isinstance(self.E_experimental, bool) or not isinstance(self.E_experimental, Real)
                or not math.isfinite(self.E_experimental) or self.E_experimental <= 0):
            raise ValueError(
                f"E_experimental deve ser um número maior que zero ou None. "
                f"Recebido: {self.E_experimental!r}."
            )
        soma = sum(c.fracao for c in self._constituintes(com_zti=self.tem_zti))
        if abs(soma - 1) > TOLERANCIA_SOMA:
            raise ValueError(
                f"A soma das frações sólidas deve ser 1 (100%). Recebido: {soma:.4f}. "
                "Ajuste as frações (os poros ficam de fora dessa soma)."
            )

    @property
    def tem_zti(self) -> bool:
        return self.zti_miudo is not None

    def _constituintes(self, com_zti: bool) -> Tuple[Constituinte, ...]:
        base = (self.pasta, self.agregado_miudo, self.agregado_graudo)
        return base + ((self.zti_miudo, self.zti_graudo) if com_zti else ())

    def fracao_poros(self, com_zti: bool) -> float:
        """Fração dos poros no último nível: poros / (sólidos considerados + poros)."""
        solidos = sum(c.fracao for c in self._constituintes(com_zti))
        return self.poros / (solidos + self.poros)

    @classmethod
    def li_2019(cls) -> 'FasesConcreto':
        """Concreto de Li et al. (2019), Tabela 3 da tese. Módulos em GPa."""
        return cls(
            pasta=Constituinte(FaseMecanica(21.34, 0.25), 0.1540),
            agregado_miudo=Constituinte(FaseMecanica(77.60, 0.15), 0.2690),
            agregado_graudo=Constituinte(FaseMecanica(51.31, 0.15), 0.4030),
            zti_miudo=Constituinte(FaseMecanica(12.70, 0.25), 0.1510),
            zti_graudo=Constituinte(FaseMecanica(10.17, 0.30), 0.0230),
            poros=0.0242,
            E_experimental=34.50,
        )


@dataclass(frozen=True)
class NivelHomogeneizacao:
    """Um nível: as fases (matriz primeiro), as frações no nível e o resultado."""
    nome: str
    fases: Tuple[str, ...]
    fracoes: Tuple[float, ...]
    modelo: str
    resultado: ResultadoMecanico


@dataclass(frozen=True)
class ResultadoMultiescala:
    """Os níveis de homogeneização em ordem; o último dá as propriedades do concreto."""
    niveis: Tuple[NivelHomogeneizacao, ...]
    E_experimental: Optional[float] = None

    @property
    def resultado(self) -> ResultadoMecanico:
        """Resultado do último nível (o concreto)."""
        return self.niveis[-1].resultado

    @property
    def Eh(self) -> float:
        return self.resultado.Eh

    @property
    def erro_relativo(self) -> Optional[float]:
        """(Ec - Eexp) / Eexp, ou None sem E experimental."""
        if self.E_experimental is None:
            return None
        return (self.Eh - self.E_experimental) / self.E_experimental


def _fase_de(resultado: ResultadoMecanico) -> FaseMecanica:
    return FaseMecanica(resultado.Eh, resultado.vh)


def _nome_modelo(modelo) -> str:
    return getattr(modelo, 'tipo', None) or type(modelo).__name__


def _nivel_tres_fases(nome, nomes, matriz, inclusao, revestimento, modelo):
    """Nível de três fases: as frações no concreto viram frações no nível."""
    soma = matriz.fracao + inclusao.fracao + revestimento.fracao
    fi_n, fr_n = inclusao.fracao / soma, revestimento.fracao / soma
    composito = CompositoRevestido(matriz.fase, inclusao.fase, revestimento.fase, fi_n, fr_n)
    return NivelHomogeneizacao(nome, nomes, (1 - fi_n - fr_n, fi_n, fr_n),
                               _nome_modelo(modelo), modelo.homogeneizar(composito))


def _nivel_duas_fases(nome, nomes, matriz, inclusao, modelo):
    fi_n = inclusao.fracao / (matriz.fracao + inclusao.fracao)
    composito = Composito(matriz.fase, inclusao.fase, fi_n)
    return NivelHomogeneizacao(nome, nomes, (1 - fi_n, fi_n),
                               _nome_modelo(modelo), modelo.homogeneizar(composito))


def calcular_concreto(fases: FasesConcreto, modelo, com_zti: bool = True,
                      modelo_poros=None) -> ResultadoMultiescala:
    """Homogeneíza o concreto em níveis (3, ou 2 se ``fases.poros == 0``).

    ``modelo`` é de três fases (QuatroFases, MultiplasFases) quando
    ``com_zti``; senão, qualquer modelo mecânico de duas fases. Sem ZTI as
    ZTIs informadas são ignoradas e as frações renormalizadas. Os poros entram
    no último nível com ``modelo_poros`` (Mori-Tanaka por padrão).
    """
    if not isinstance(fases, FasesConcreto):
        raise ValueError(f"fases deve ser FasesConcreto. Recebido: {type(fases).__name__}.")
    modelo_poros = MoriTanaka() if modelo_poros is None else modelo_poros
    if not isinstance(modelo_poros, ModeloMecanico):
        raise ValueError(
            f"modelo_poros deve ser um modelo mecânico de duas fases (ex.: MoriTanaka()). "
            f"Recebido: {_nome_modelo(modelo_poros)}."
        )

    if com_zti:
        if not fases.tem_zti:
            raise ValueError(
                "com_zti=True exige zti_miudo e zti_graudo em FasesConcreto. "
                "Informe as ZTIs ou use com_zti=False."
            )
        if not isinstance(modelo, ModeloTresFases):
            raise ValueError(
                f"Com ZTI o modelo deve ser de três fases (QuatroFases ou MultiplasFases). "
                f"Recebido: {_nome_modelo(modelo)}."
            )
        n1 = _nivel_tres_fases('Argamassa', ('Pasta de cimento', 'Agregado miúdo', 'ZTI-2'),
                               fases.pasta, fases.agregado_miudo, fases.zti_miudo,
                               modelo)
        argamassa = Constituinte(_fase_de(n1.resultado),
                                 fases.pasta.fracao + fases.agregado_miudo.fracao
                                 + fases.zti_miudo.fracao)
        n2 = _nivel_tres_fases('Concreto', ('Argamassa', 'Agregado graúdo', 'ZTI-1'),
                               argamassa, fases.agregado_graudo, fases.zti_graudo,
                               modelo)
    else:
        if not isinstance(modelo, ModeloMecanico):
            raise ValueError(
                f"Sem ZTI o modelo deve ser de duas fases (ex.: MoriTanaka(), GSC()). "
                f"Recebido: {_nome_modelo(modelo)}."
            )
        n1 = _nivel_duas_fases('Argamassa', ('Pasta de cimento', 'Agregado miúdo'),
                               fases.pasta, fases.agregado_miudo, modelo)
        argamassa = Constituinte(_fase_de(n1.resultado),
                                 fases.pasta.fracao + fases.agregado_miudo.fracao)
        n2 = _nivel_duas_fases('Concreto', ('Argamassa', 'Agregado graúdo'),
                               argamassa, fases.agregado_graudo, modelo)
    niveis = (n1, n2)

    if fases.poros > 0:
        fp = fases.fracao_poros(com_zti)
        composito = Composito(_fase_de(n2.resultado), FaseMecanica.poro(POISSON_POROS), fp)
        niveis += (NivelHomogeneizacao('Concreto com poros', ('Concreto', 'Poros'),
                                       (1 - fp, fp), _nome_modelo(modelo_poros),
                                       modelo_poros.homogeneizar(composito)),)
    return ResultadoMultiescala(niveis, fases.E_experimental)
