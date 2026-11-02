[![Release](https://img.shields.io/badge/release-v1.0.0-orange)](https://github.com/CllsPy/HOOP/releases)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)](https://streamlit.io)

# HOOP

> A Python framework for micromechanical homogenization of composite materials, based on the framework proposed by Silva (2022).

HOOP computes the effective elastic properties (and, through the API, the effective thermal conductivity) of two-phase composites with classical micromechanical models. It ships as an installable package, `hoop`, with a programmatic API and a Streamlit interface.


## Table of Contents

- [Installation](#installation)
- [Running the Interface](#running-the-interface)
- [Programmatic API](#programmatic-api)
- [Architecture](#architecture)
- [Micromechanical Models](#micromechanical-models)
- [Example Scripts](#example-scripts)
- [Running Tests](#running-tests)
- [Design System](#design-system)
- [Contributing](#contributing)
- [References](#references)
- [License](#license)


## Installation

**Requirements:** Python 3.9+

```bash
git clone https://github.com/CllsPy/HOOP.git
cd HOOP
pip install -e .          # the hoop package and its runtime dependencies
pip install -e ".[dev]"   # the same, plus pytest
```

Runtime dependencies (declared in `pyproject.toml`, mirrored in `requirements.txt`): `numpy`, `scipy`, `matplotlib`, `seaborn`, `pandas`, `streamlit`, `Pillow`, `fpdf2`.

The project uses a src layout: the code lives in `src/hoop/` and is imported as `hoop.<subpackage>` (for example `from hoop.micmodelos.gsc import GSC`). Install the package before running anything; no `sys.path` tweaks are needed.


## Running the Interface

From the repository root:

```bash
streamlit run src/app.py
```

`src/app.py` is a thin entry point that calls `hoop.ui.app.main()`. Run it from the root so Streamlit picks up the theme in `.streamlit/config.toml`.

The interface is a three-step flow, shown in the sidebar:

1. **Dados (Data):** pick a material preset (concrete, glass/epoxy, steel/tungsten carbide, carbon/epoxy, polymer/steel spheres) or enter custom matrix and inclusion properties (E in MPa, Poisson's ratio), the maximum inclusion fraction and the models to compare, then calculate. Mechanical analysis with spherical inclusions is enabled. Cylinder, disk and conductivity are shown but still under validation.
2. **Análise (Analysis):** compare the curves of every model (Eh, Eh/Em or νh against fi), read values at a chosen fi, inspect each model individually and see the full table. Models that fail at some fi keep the curve computed up to that point and show the error. Dilute Suspension is flagged beyond its validity range (fi ≈ 0.10).
3. **Relatório (Report):** choose a title, author and sections (combined chart, value table, one chart per model) and download the PDF.

The Analysis and Report steps unlock after the first calculation. If the data changes afterwards, both steps warn you to recalculate.

A segmented control at the top of Dados switches between **Duas fases** (two phases, the default flow above) and **Concreto multiescala** (multiscale concrete). In the concrete mode:

1. **Dados:** cards for cement paste, fine aggregate, its ITZ (ZTI-2), coarse aggregate and its ITZ (ZTI-1), each with E (MPa), ν and volume fraction in the concrete (%), plus pores (% of solids) and an optional experimental E. Choose **Com ZTI** (Quatro fases and/or Múltiplas fases) or **Sem ZTI** (any two-phase model, with Mori-Tanaka or the same model for the pores). Defaults are Li et al. (2019), restorable with "Restaurar valores da tese". A preview shows the corrected fractions of each level.
2. **Análise:** E of the concrete and the error against the experimental value, E per level (one line per model, dashed experimental reference), a Table 6/8-style table and E, ν, K, G per level (CSV). A model that fails (e.g. Reuss in the pores) shows an error and keeps the levels it reached; the others are unaffected.
3. **Relatório:** PDF with phases, fractions per level, the chart, the results table and the error.

Each mode keeps its own input and result.


## Programmatic API

### Stateless homogenization

Describe the problem as an immutable `Composito` and ask a model for a result. Phases and composites are frozen dataclasses that validate on creation (E > 0 except for pores built with `FaseMecanica.poro()`, -1 < ν < 0.5, 0 ≤ fi ≤ 1, known geometry). Models keep no state between calls.

```python
from dataclasses import replace

from hoop.homogenizacao.composito import Composito
from hoop.materiais.fases import FaseCondutividade, FaseMecanica
from hoop.micmodelos.micmodelos import homogeneizar
from hoop.micmodelos.moritanaka import MoriTanaka

c = Composito(matriz=FaseMecanica(E=30_000, v=0.20),
              inclusao=FaseMecanica(E=70_000, v=0.30),
              fi=0.3, geometria='esfera')        # 'esfera', 'cilindro' or 'disco'
r = MoriTanaka().homogeneizar(c)                 # ResultadoMecanico(Eh, vh, kh, Gh, Em, fi, C)
r50 = MoriTanaka().homogeneizar(replace(c, fi=0.5))  # replace() validates again

k = Composito(FaseCondutividade.isotropica(1.0), FaseCondutividade.isotropica(20.0), fi=0.3)
MoriTanaka().homogeneizar_condutividade(k)       # ResultadoCondutividade(K11, K22, K33, fi, kh)

homogeneizar(MoriTanaka(), k)                    # picks the method from the phase type
```

`ResultadoMecanico` holds `Eh`, `vh`, `kh`, `Gh` (MPa), `Em`, `fi` and the 6×6 stiffness tensor `C` in Voigt notation. `ResultadoCondutividade` holds `K11`, `K22`, `K33`, `fi` and the 3×3 tensor `kh`.

### Sweeping the inclusion fraction

`varrer` computes one scalar over fi = 0 … `fi_max` and returns a `Curva(xs, ys, nome)`. It never changes the composite or the model.

```python
from hoop.homogenizacao.varredura import varrer
from hoop.micmodelos.gsc import GSC

curva = varrer(c, GSC(), extrair=lambda r: r.Eh / r.Em, fi_max=0.6, passos=60)
```

### Concreto multiescala (multiscale concrete)

Concrete is homogenized in levels, as in Silva (2022), Section 3.1: cement paste + fine aggregate (mortar), mortar + coarse aggregate, then concrete + pores. With interfacial transition zones (ITZ/ZTI) each aggregate is coated by its ZTI and a three-phase model is used (`QuatroFases`, Li et al. 1999, or `MultiplasFases`, Shi et al. 2020); without ZTI any two-phase model works. Phase fractions are given in the concrete and corrected per level automatically. Pores are a zero-stiffness phase created only by `FaseMecanica.poro()` and enter the last level with Mori-Tanaka by default.

```python
from hoop.homogenizacao.multiescala import FasesConcreto, calcular_concreto
from hoop.micmodelos.moritanaka import MoriTanaka
from hoop.micmodelos.quatrofases import QuatroFases

fases = FasesConcreto.li_2019()                  # Table 3 of the thesis, E in GPa
r = calcular_concreto(fases, QuatroFases())      # with ZTI, 3 levels
for nivel in r.niveis:
    print(nivel.nome, dict(zip(nivel.fases, nivel.fracoes)), round(nivel.resultado.Eh, 3))
print(r.Eh, r.erro_relativo)                     # 34.645 GPa, +0.42 % against 34.50 GPa

calcular_concreto(fases, MoriTanaka(), com_zti=False).Eh   # 45.671 GPa (Table 6)
```

Reuss and Popovic refuse pores (`ValueError`): with E = 0 their result is null or singular. A pore can never be a matrix.

### Plotting

`DesenhoMecanico` draws property-versus-fi curves. Each call creates and **returns** a matplotlib `Figure`. Nothing opens a window: call `plt.show()` or `fig.savefig(...)` yourself. Styles: `'fixar_fracao'` (Eh), `'normalizar'` (Eh/Em) and `'poisson'` (νh). `DesenhoCondutividade('K11' | 'K22' | 'K33')` does the same for conductivity.

`desenha` takes a `Homogenizacao` (the legacy configuration object below). The helper `hoop.exemplos.criar_analise` builds one from four numbers.

```python
import matplotlib.pyplot as plt

from hoop.desenho.desenho_mec import DesenhoMecanico
from hoop.exemplos import MATERIAIS, criar_analise
from hoop.micmodelos.gsc import GSC
from hoop.micmodelos.moritanaka import MoriTanaka

h = criar_analise(**MATERIAIS['concreto'])       # fi = 0 sweeps the full range 0 → 1
d = DesenhoMecanico(estilo='normalizar')
d.desenha(h, modelo=GSC())                       # Figure with one curve
d.desenha(h, modelo=MoriTanaka())
fig = d.juntar_grafs()                           # Figure with every curve drawn so far
fig.savefig('comparacao.png')
plt.show()                                       # only if you want windows
```

### PDF reports

The interface report can be generated without running the Streamlit app. `hoop.ui.calculo.calcular` computes the curves from an `EntradaComposito`, and `gerar_pdf` returns the PDF bytes:

```python
from hoop.ui.calculo import calcular
from hoop.ui.entrada import EntradaComposito
from hoop.ui.relatorio_analise import OpcoesRelatorio, gerar_pdf

resultado = calcular(EntradaComposito(Em=30_000, vm=0.20, Ei=70_000, vi=0.30, fi_max=0.6))
pdf = gerar_pdf(resultado, OpcoesRelatorio(titulo='Concrete', grandeza='Eh/Em',
                                           graficos_por_modelo=True))
open('concrete.pdf', 'wb').write(pdf)
```

The older `hoop.relatorio.gerar_relatorio(objH, d, filename)` still writes a PDF from a `DesenhoMecanico` with curves already drawn. The example scripts use it.

### Legacy adapter

`Homogenizacao` with `Mecanico`/`Condutividade` phases in `matH` is still supported. It builds its `Composito` through `objH.composito()`, and `modelo.calc(objH)` copies the result onto the old attributes (`Eh`, `vh`, `C`, `K11`, ...). New code should use `Composito` directly.

```python
from hoop.homogenizacao.homogenizacao import Homogenizacao
from hoop.mecanico.mecanico import Mecanico

h = Homogenizacao()
h.tipo, h.analise_tipo, h.geo = 'global', 'mecanica', 'esfera'
h.Em, h.vm, h.Ei, h.vi = 70_000, 0.33, 210_000, 0.30
h.set_analise()
m1 = Mecanico(); m1.E, m1.v, m1.geo = h.Em, h.vm, h.geo
m2 = Mecanico(); m2.E, m2.v, m2.geo = h.Ei, h.vi, h.geo
h.matH.extend([m1, m2])
```

### Extending

**A new model:** subclass `Micmodelos` plus the mixins of the analyses it supports, and implement the stateless methods. The legacy `calc(objH)` adapter comes for free.

```python
from hoop.micmodelos.micmodelos import Micmodelos
from hoop.micmodelos.protocolos import ModeloMecanico

class MeuModelo(Micmodelos, ModeloMecanico):
    def __init__(self):
        super().__init__()
        self.tipo = 'MeuModelo'

    def homogeneizar(self, composito):
        Cm, Ci = composito.matriz.L, composito.inclusao.L   # read-only 6×6 tensors
        S = composito.eshelby                               # Eshelby tensor of the inclusion
        C_h = ...                                           # homogenized tensor
        return self._resultado_do_tensor(composito, C_h)
```

**A new plot style:** subclass `EstiloGrafico` and register it.

```python
from hoop.desenho.estilos.estilo_base import EstiloGrafico
from hoop.desenho.estilos.estilo_registry import EstiloRegistry

class EstiloCisalhamento(EstiloGrafico):
    nome = 'cisalhamento'
    titulo = 'Módulo de cisalhamento'
    rotulo_y = 'Gh [MPa]'

    def extrair(self, resultado) -> float:
        return resultado.Gh

EstiloRegistry.registrar(EstiloCisalhamento())
```

New geometries are registered the same way in `hoop.mecanico.geometria_registry.GeometriaRegistry`.


## Architecture

```
pyproject.toml                    # package metadata (hoop 1.0.0), dependencies, extras [dev]
.streamlit/config.toml            # Streamlit theme (design system tokens)
src/
├── app.py                        # thin Streamlit entry point → hoop.ui.app.main()
├── Milled.py                     # exploratory script (legacy API)
├── cases/                        # runnable example scripts (see below)
└── hoop/
    ├── exemplos.py               # MATERIAIS presets + criar_analise() helper
    ├── materiais/
    │   ├── fases.py              # FaseMecanica, FaseCondutividade (immutable phases)
    │   ├── materiais.py          # Materiais: base of the legacy phase objects
    │   └── condutividade.py      # Condutividade (legacy conductivity phase)
    ├── mecanico/
    │   ├── tensores.py           # isotropic stiffness, Hill tensor, K/G ↔ E/ν
    │   ├── geometrias.py         # Eshelby tensors per geometry
    │   ├── geometria_registry.py # GeometriaRegistry, tensor_eshelby()
    │   └── mecanico.py           # Mecanico (legacy mechanical phase)
    ├── homogenizacao/
    │   ├── composito.py          # Composito (immutable two-phase composite)
    │   ├── varredura.py          # varrer() → Curva
    │   ├── homogenizacao.py      # Homogenizacao (legacy adapter)
    │   └── calculadora_fracoes.py
    ├── analise/analise.py        # Analise: legacy analysis configuration
    ├── micmodelos/               # Voigt, Reuss, Dilute, Mori-Tanaka, SC, GSC, Popovic
    │   ├── micmodelos.py         # Micmodelos base class + homogeneizar(modelo, composito)
    │   └── protocolos.py         # ModeloMecanico / ModeloCondutividade mixins
    ├── resultados/resultados.py  # ResultadoMecanico / ResultadoCondutividade (frozen)
    ├── desenho/
    │   ├── desenho_mec.py        # DesenhoMecanico: returns matplotlib Figures
    │   ├── desenho_cond.py       # DesenhoCondutividade
    │   └── estilos/              # EstiloRegistry + fixar_fracao, normalizar, poisson, condutividade_*
    ├── relatorio/
    │   └── relatorio.py, extrator.py, gerador_graficos.py, construtor_pdf.py
    │                             # gerar_relatorio(objH, d, filename) (legacy report)
    └── ui/
        ├── app.py                # main(): page setup, sidebar step map, page dispatch
        ├── entrada.py            # EntradaComposito, presets, validation (no Streamlit)
        ├── formatacao.py         # pt-BR number formatting and parsing
        ├── estado.py             # st.session_state: step, input, result, reading
        ├── acoes.py              # calculate with progress, register, rerun
        ├── relatorio_analise.py  # gerar_pdf(resultado, opcoes) → bytes (interface report)
        ├── pdf_hoop.py           # PaginaHOOP: fpdf2 page with the design system
        ├── calculo.py            # MODELOS catalog, calcular() → ResultadoAnalise (no Streamlit)
        ├── concreto.py           # EntradaConcreto, validation, level preview, calcular_concreto_ui (no Streamlit)
        ├── relatorio_multiescala.py  # gerar_pdf_concreto(resultado, opcoes) → bytes
        ├── graficos.py           # interface figures
        ├── tema.py               # colors, series, glyphs, fonts, CSS
        ├── componentes.py        # reusable widgets
        └── paginas/              # dados.py, analise.py, relatorio.py: render()
                                  # dados_concreto.py, analise_concreto.py, relatorio_concreto.py
tests/                            # pytest suite
```

**Design notes**

- **Immutable core:** phases, composites and results are frozen dataclasses. The phase tensors are read-only arrays. Models are stateless.
- **Registries:** `EstiloRegistry` and `GeometriaRegistry` add styles and geometries without editing existing code.
- **Mixins:** `ModeloMecanico` and `ModeloCondutividade` declare which analyses a model supports. `homogeneizar(modelo, composito)` dispatches on the phase type.
- **Calculation apart from presentation:** `varrer` and `hoop.ui.calculo` compute. `desenho`, `ui.graficos` and `relatorio` only draw.
- **Conventions:** `fi` is the inclusion fraction and `fm = 1 - fi` the matrix fraction. Mechanical tensors are 6×6 in Voigt notation (σ = C:ε), conductivity tensors are 3×3 (q = K·∇T). E is in MPa.


## Micromechanical Models

The seven two-phase models support both mechanical and conductivity analysis through the API. The three-phase models take a `CompositoRevestido(matriz, inclusao, revestimento, fi, fr)`.

| Model | Class | Family | Notes |
|---|---|---|---|
| Voigt | `Voigt` | Bound | Upper bound: uniform strain |
| Reuss | `Reuss` | Bound | Lower bound: uniform stress |
| Dilute Suspension | `DiluteSuspension` | Mean field | Isolated inclusions, valid for fi ≲ 0.10 |
| Mori-Tanaka | `MoriTanaka` | Mean field | Accounts for interaction between inclusions |
| Self-Consistent | `SelfConsistent` | Self-consistent | Iterative. Raises `RuntimeError` if it does not converge |
| GSC | `GSC` | Self-consistent | Composite sphere assemblage (Christensen and Lo) |
| Popovic | `Popovic` | Average | Arithmetic mean of Voigt and Reuss |
| Quatro-Fases | `QuatroFases` | Three-phase | Coated spheres: GSC(coating + inclusion), then GSC(matrix + core). Mechanical only |
| Múltiplas-Fases | `MultiplasFases` | Three-phase | Coated inclusions, double-inclusion tensors (Shi et al., 2020), as in the author's code. Requires fr / fi ≤ 1. Mechanical only |

**Mechanical equations**

```
Voigt:        C_h = fi C_i + (1 - fi) C_m
Reuss:        C_h = [fi C_i⁻¹ + (1 - fi) C_m⁻¹]⁻¹
Dilute:       A = [I + S C_m⁻¹ (C_i - C_m)]⁻¹,  C_h = C_m + fi (C_i - C_m) A
Mori-Tanaka:  C_h = C_m + fi (C_i - C_m) A [fi A + (1 - fi) I]⁻¹
GSC (bulk):   K_h = K_m + fi (K_i - K_m)(3K_m + 4G_m) / (3K_m + 4G_m + 3(1 - fi)(K_i - K_m))
              G_h is the root of the Christensen–Lo quadratic.
E and ν:      E_h = 9 K_h G_h / (3 K_h + G_h),  ν_h = (3 K_h - 2 G_h) / (2 (3 K_h + G_h))
```


## Example Scripts

`src/cases/` holds runnable studies built on `hoop.exemplos` and the legacy API. Each one draws figures, and some write a PDF to the current directory:

| Script | What it shows |
|---|---|
| `case_todos_modelos.py` | all seven models on one system |
| `case_fixar_fracao.py` | Eh vs fi |
| `case_normalizar.py` | Eh/Em vs fi |
| `case_poisson.py` | νh vs fi |
| `case_contraste.py` | effect of the stiffness contrast Ei/Em (Mori-Tanaka) |
| `case_geometrias.py` | sphere vs cylinder vs disk (Mori-Tanaka) |

```bash
python src/cases/case_todos_modelos.py
MPLBACKEND=Agg python src/cases/case_contraste.py   # no windows
```

`src/Milled.py` is an exploratory script. With its current inclusion modulus (`Ei = 0.1` MPa, not yet confirmed), Self-Consistent stops with a `RuntimeError` because it does not converge.


## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

The suite checks each model against the Voigt/Reuss bounds and the pure-phase limits. It validates Self-Consistent against a direct solution of Hill's equations and checks known values for concrete. It also checks that the core is immutable, that the stateless API and the legacy adapter give identical results, and it drives the Streamlit app with `streamlit.testing` (each step, the full flow and PDF generation).


## Design System

The interface and the PDF share one set of tokens, defined in `src/hoop/ui/tema.py`. The Streamlit side lives in [`.streamlit/config.toml`](.streamlit/config.toml).

| Token | Value | Use |
|---|---|---|
| `accent` | `#0B6E6E` | primary actions, links, Mori-Tanaka series |
| `ink` / `ink-muted` | `#142120` / `#4F5E5C` | text |
| `surface-0` / `surface-1` / `surface-2` | `#F6F7F5` / `#FFFFFF` / `#ECEFEC` | backgrounds |
| `line` | `#D5DBD8` | borders |
| `phase-matrix` / `phase-inclusion` | `#3E6F8A` / `#A85A0C` | matrix and inclusion labels |
| `success` / `warning` / `danger` | `#2E7D4F` / `#9A5800` / `#B3261E` | states |
| series | bounds `#6E7C7A`, SC `#C2620F`, GSC `#2F55C8`, Dilute `#8E3B8A`, Popovic `#5F7316`, Quatro fases `#9F2F4F`, Múltiplas fases `#5B4FB0` | one fixed color (plus dash and marker) per model |
| concrete phases | paste `#3E6F8A`, fine `#7D4E1E`, coarse `#A85A0C`, ITZ `#6F6A58`, pores `#8F9C99` | paste in the matrix family, aggregates in the inclusion family, ITZs and pores neutral |

- **Type:** Archivo (headings), Source Sans 3 (text), IBM Plex Mono (numbers and code), loaded from Google Fonts.
- **Icons:** Material Symbols in Streamlit (`:material/bubble_chart:` as the page icon), plus inline SVG glyphs for the inclusion geometries (sphere, cylinder, disk) in `GLIFOS`.


## Contributing

Contributions are welcome. Please open an issue first to discuss the change.

Open areas:

- validation of cylinder and disk geometries, then enabling them in the interface
- conductivity analysis in the interface
- third-phase support
- thermomechanical expansion coefficients
- more models (Halpin-Tsai, Hashin-Shtrikman, ...)

Code conventions: names in Portuguese, as in the rest of the code. `fi` = inclusion fraction, `fm` = matrix fraction. Every change keeps the test suite green.


## References

- Silva, R. (2022). *Framework for micromechanical homogenization of composite materials.*
- Mori, T. & Tanaka, K. (1973). Average stress in matrix and average elastic energy of materials with misfitting inclusions. *Acta Metallurgica*, 21(5), 571–574.
- Eshelby, J. D. (1957). The determination of the elastic field of an ellipsoidal inclusion. *Proc. R. Soc. London A*, 241, 376–396.
- Christensen, R. M. & Lo, K. H. (1979). Solutions for effective shear properties in three phase sphere and cylinder models. *J. Mech. Phys. Solids*, 27(4), 315–330.


## License

This project is licensed under the MIT License.
