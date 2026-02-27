[![Release](https://img.shields.io/badge/release-v1.0.0-orange)](https://github.com/CllsPy/HOOP/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)](https://streamlit.io)

# HOOP 

> A Python framework for micromechanical homogenization of composite materials, based on the framework proposed by Silva (2022).

HOOP computes effective mechanical (elastic) and thermal (conductivity) properties of composite materials using classical micromechanical models. It provides both a programmatic API and an interactive Streamlit web interface.



## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Running the Web App](#running-the-web-app)
  - [Using the API](#using-the-api)
  - [Generating a PDF Report](#generating-a-pdf-report)
- [Architecture](#architecture)
- [Micromechanical Models](#micromechanical-models)
- [Analysis Types](#analysis-types)
- [Plot Styles](#plot-styles)
- [Contributing](#contributing)
- [License](#license)



## Overview

Composite materials are used across engineering — from concrete and asphalt to aerospace components. Predicting their effective properties from constituent phases is a fundamental problem in materials science. HOOP implements several well-established micromechanical homogenization models in a unified, extensible framework.

The pipeline is:

```
Homogenizacao → Micmodelos → DesenhoMecanico
```

A `Homogenizacao` object holds the material phases (`Mecanico` or `Condutividade` instances), the analysis configuration (`Analise`), and delegates computation to the chosen micromechanical model. Results are visualized via `DesenhoMecanico` and can be exported to PDF via `gerar_relatorio`.



## Features

- **7 micromechanical models** for mechanical analysis: Voigt, Reuss, Dilute Suspension, Mori-Tanaka, Self-Consistent, GSC, and Popovic
- **3 inclusion geometries**: sphere, cylinder, disk (via Eshelby tensor)
- **3 plot styles**: Young's modulus vs. volume fraction, normalized modulus (Eh/Em), and Poisson's ratio
- **Thermal conductivity** analysis (Voigt, Reuss, Self-Consistent, GSC)
- **PDF report generation** with input data, combined plot, and per-model results
- **Streamlit web interface** with dark theme and interactive model selection
- **Extensible design**: add new models and plot styles without modifying existing code



## Installation

**Requirements:** Python 3.8+

```bash
git clone https://github.com/CllsPy/HOOP.git
cd HOOP
pip install -r requirements.txt
```

Dependencies: `numpy`, `scipy`, `matplotlib`, `seaborn`, `pandas`, `streamlit`, `Pillow`, `fpdf2`.



## Quick Start

```python
from homogenizacao.homogenizacao import Homogenizacao
from mecanico.mecanico import Mecanico
from desenho.desenho_mec import DesenhoMecanico
from micmodelos.gsc import GSC
from micmodelos.moritanaka import MoriTanaka

# Configure analysis
h1 = Homogenizacao()
h1.tipo         = 'global'
h1.analise_tipo = 'mecanica'
h1.geo          = 'esfera'
h1.Em, h1.vm    = 41000, 0.2   # matrix: E [MPa], Poisson
h1.Ei, h1.vi    = 250000, 0.25  # inclusion: E [MPa], Poisson
h1.set_analise()

# Define material phases
m1 = Mecanico(); m1.E = h1.Em; m1.v = h1.vm; m1.geo = h1.analH.geo  # matrix
m2 = Mecanico(); m2.E = h1.Ei; m2.v = h1.vi; m2.geo = h1.analH.geo  # inclusion
h1.matH.extend([m1, m2])

# Plot models
d = DesenhoMecanico(estilo='normalizar')
d.desenha(h1, modelo=GSC())
d.desenha(h1, modelo=MoriTanaka())
d.juntar_grafs(h1)
```



## Usage

### Running the Web App

```bash
cd src
streamlit run app.py
```

The web interface allows you to:
- Select analysis type (mechanical or conductivity)
- Set inclusion geometry (sphere, cylinder, disk)
- Input matrix and inclusion properties
- Choose which micromechanical models to compare
- Select the plot style
- Download a PDF report

### Using the API

All source code lives under `src/`. Run scripts from `src/` so Python resolves bare-name imports:

```bash
cd src
python Milled.py
```

**Setting up a two-phase analysis:**

```python
h1 = Homogenizacao()
h1.tipo         = 'global'
h1.analise_tipo = 'mecanica'    # 'mecanica' or 'condutividade'
h1.geo          = 'esfera'      # 'esfera', 'cilindro', or 'disco'
h1.Em, h1.vm    = 70000, 0.33   # matrix properties
h1.Ei, h1.vi    = 210000, 0.30  # inclusion properties
h1.set_analise()

m1 = Mecanico(); m1.E = h1.Em; m1.v = h1.vm; m1.geo = h1.analH.geo
m2 = Mecanico(); m2.E = h1.Ei; m2.v = h1.vi; m2.geo = h1.analH.geo
h1.matH.extend([m1, m2])
```

**Plotting individual models:**

```python
d = DesenhoMecanico(estilo='fixar_fracao')  # 'fixar_fracao', 'poisson', 'normalizar'
d.desenha(h1, modelo=Voigt())
d.desenha(h1, modelo=Reuss())
d.desenha(h1, modelo=GSC())
```

Each `desenha()` call opens its own figure window. Call `juntar_grafs()` to see all models overlaid:

```python
d.juntar_grafs(h1)
```

### Generating a PDF Report

After plotting, generate a PDF with input data, combined chart, and per-model results:

```python
from relatorio.relatorio import gerar_relatorio

d.desenha(h1, modelo=GSC())
d.desenha(h1, modelo=MoriTanaka())
d.juntar_grafs(h1)

gerar_relatorio(h1, d, filename='report.pdf')
```

The report includes:
1. **Input Data** — analysis type, geometry, plot style, Em, vm, Ei, vi, fi range
2. **Combined Chart** — all models overlaid
3. **Per-Model Results** — table with values at fi = 0.5 and fi = max, plus individual chart


## Architecture

```
src/
├── app.py                        # Streamlit entry point
├── analise/analise.py            # Analise: analysis config (type, geometry, fractions)
├── materiais/materiais.py        # Materiais: base class for material phases
├── mecanico/
│   ├── mecanico.py               # Mecanico(Materiais): computes L, P, S tensors
│   ├── geometrias.py             # Eshelby tensors per geometry
│   └── geometria_registry.py     # Registry pattern for geometries
├── homogenizacao/
│   ├── homogenizacao.py          # Homogenizacao: orchestrator
│   └── calculadora_fracoes.py    # Volume fraction distribution
├── micmodelos/
│   ├── micmodelos.py             # Micmodelos: abstract base class
│   ├── protocolos.py             # ModeloMecanico / ModeloCondutividade mixins
│   ├── voigt.py                  # Voigt upper bound
│   ├── reuss.py                  # Reuss lower bound
│   ├── dilute.py                 # Dilute Suspension
│   ├── moritanaka.py             # Mori-Tanaka
│   ├── selfconsistent.py         # Self-Consistent (iterative)
│   ├── gsc.py                    # Generalized Self-Consistent
│   └── popovic.py                # Popovic (Voigt-Reuss average)
├── desenho/
│   ├── desenho_mec.py            # DesenhoMecanico: plot engine
│   └── estilos/                  # Strategy pattern: fixar_fracao, poisson, normalizar
├── resultados/resultados.py      # ResultadoMecanico / ResultadoCondutividade dataclasses
└── relatorio/
    ├── relatorio.py              # gerar_relatorio() entry point
    ├── extrator.py               # Data extraction into pure dataclasses
    ├── gerador_graficos.py       # Matplotlib → PNG bytes (via BytesIO)
    └── construtor_pdf.py         # PDF assembly with fpdf2
```

**Key design patterns:**
- **Registry** — `EstiloRegistry` and `GeometriaRegistry` allow extensible registration of styles and geometries without modifying existing code
- **Strategy** — `EstiloGrafico` protocol separates data collection from rendering
- **Mixins** — `ModeloMecanico` and `ModeloCondutividade` decouple analysis types
- **Abstract Base Class** — `Micmodelos` enforces the `calc(objH)` interface on all models

### Tensors

All mechanical tensors are 6×6 NumPy arrays in Voigt notation (σ = C:ε). Conductivity tensors are 3×3 (q = K·∇T).

### Volume Fractions

- `fi` — inclusion fraction
- `fm` — matrix fraction
- `fr` — third phase fraction (reinforcement), optional
- Constraint: `fi + fm + fr = 1.0`

### Material Phases in `matH`

| Index | Phase |
|---|---|
| `matH[0]` | Matrix |
| `matH[1]` | Inclusion |
| `matH[2]` | Third phase (optional) |



## Micromechanical Models

| Model | Class | Type | Notes |
|---|---|---|---|
| Voigt | `Voigt` | Bound | Upper bound — uniform strain assumption |
| Reuss | `Reuss` | Bound | Lower bound — uniform stress assumption |
| Dilute Suspension | `DiluteSuspension` | Mean-field | Valid for low fi (< ~10%) |
| Mori-Tanaka | `MoriTanaka` | Mean-field | Accounts for inclusion interaction |
| Self-Consistent | `SelfConsistent` | Self-consistent | Iterative, valid for wide fi range |
| GSC | `GSC` | Generalized SC | Composite sphere assemblage |
| Popovic | `Popovic` | Average | Arithmetic mean of Voigt and Reuss bounds |

### Model Equations (Mechanical)

**Voigt:**
```
C_h = fi * C_i + (1 - fi) * C_m
```

**Reuss:**
```
C_h = [fi * C_i⁻¹ + (1 - fi) * C_m⁻¹]⁻¹
```

**Dilute Suspension:**
```
A = [I + S * C_m⁻¹ * (C_i - C_m)]⁻¹
C_h = C_m + fi * (C_i - C_m) * A
```

**Mori-Tanaka:**
```
C_h = C_m + fi * (C_i - C_m) * [fi * I + (1 - fi) * A_dilute]⁻¹
```

**GSC (bulk modulus K):**
```
K_h = K_m + fi * (K_i - K_m) * (3K_m + 4G_m) / (3K_m + 4G_m + 3(1-fi)(K_i - K_m))
```
Shear modulus G_h is solved from a quadratic equation in G.

**Effective Young's modulus and Poisson's ratio (from tensor C):**
```
E_h = 9 K_h G_h / (3 K_h + G_h)
v_h = (3 K_h - 2 G_h) / (2 * (3 K_h + G_h))
```


## Analysis Types

### Mechanical (`analise_tipo = 'mecanica'`)

Input per phase: Young's modulus `E` [MPa] and Poisson's ratio `v`.

Output (stored on `objH.modH`):

| Attribute | Description |
|---|---|
| `Eh` | Homogenized Young's modulus [MPa] |
| `vh` | Homogenized Poisson's ratio |
| `kh` | Homogenized bulk modulus [MPa] |
| `Gh` | Homogenized shear modulus [MPa] |
| `C` | Homogenized constitutive tensor (6×6) |

### Conductivity (`analise_tipo = 'condutividade'`)

Input per phase: thermal conductivity values `k11`, `k22`, `k33`.

Output:

| Attribute | Description |
|---|---|
| `K11`, `K22`, `K33` | Homogenized conductivity tensor components |
| `kh` | Homogenized conductivity tensor (3×3) |

---

## Plot Styles

| Style key | X axis | Y axis | Class |
|---|---|---|---|
| `'fixar_fracao'` | fi | Eh [MPa] | `EstiloFixarFracao` |
| `'normalizar'` | fi | Eh / Em | `EstiloNormalizar` |
| `'poisson'` | fi | vh | `EstiloPoisson` |

Register a custom style:

```python
from desenho.estilos.estilo_base import EstiloGrafico
from desenho.estilos.estilo_registry import EstiloRegistry

class EstiloCustom(EstiloGrafico):
    nome = 'custom'

    def coletar_ponto(self, objH, modelo, Fi):
        objH.analH.fi = Fi
        objH.calc()
        return Fi, objH.modH.Gh  # shear modulus

    def configurar_eixos(self, ax):
        ax.set_title('Shear Modulus vs fi')
        ax.set_xlabel('fi')
        ax.set_ylabel('Gh [MPa]')

EstiloRegistry.registrar(EstiloCustom())
```


## Extending with a New Model

Subclass `Micmodelos` and implement `calc(objH)`:

```python
from micmodelos.micmodelos import Micmodelos

class MyModel(Micmodelos):
    def __init__(self):
        super().__init__()
        self.tipo = 'MyModel'

    def calc(self, objH):
        if objH.analH.analise_type == 'mecanica':
            fi = objH.analH.fi
            Cm = objH.matH[0].L   # matrix stiffness tensor
            Ci = objH.matH[1].L   # inclusion stiffness tensor

            # ... compute C_h ...

            self.C  = C_h
            self.Eh = ...
            self.vh = ...
            self.kh = ...
            self.Gh = ...
```


## Contributing

Contributions are welcome. Please open an issue first to discuss what you'd like to change.

**Areas open for contribution:**
- Third-phase support in the Streamlit UI
- Cylinder and disk geometry validation
- Conductivity analysis UI completion
- Thermomechanical expansion coefficients
- Additional micromechanical models (Halpin-Tsai, Hashin-Shtrikman, etc.)

**Code conventions:**
- Comments `# <------- FUNCIONANDO` mark tested/working code
- Comments `# <------- FALTA TESTAR` mark untested code
- Volume fractions: `fi` = inclusion, `fm` = matrix, `fr` = third phase
- Tensors: 6×6 NumPy arrays in Voigt notation for mechanics; 3×3 for conductivity

## References

- Silva, R. (2022). *Framework for micromechanical homogenization of composite materials.*
- Mori, T. & Tanaka, K. (1973). Average stress in matrix and average elastic energy of materials with misfitting inclusions. *Acta Metallurgica*, 21(5), 571–574.
- Eshelby, J. D. (1957). The determination of the elastic field of an ellipsoidal inclusion. *Proc. R. Soc. London A*, 241, 376–396.
- Christensen, R. M. & Lo, K. H. (1979). Solutions for effective shear properties in three phase sphere and cylinder models. *J. Mech. Phys. Solids*, 27(4), 315–330.

---

## License

This project is licensed under the [MIT License](LICENSE).
