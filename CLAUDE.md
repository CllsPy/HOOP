# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HOOP is a Python framework for composite materials analysis, based on the framework proposed by Silva (2022). It provides micromechanical homogenization models for computing effective mechanical (elastic) and thermal (conductivity) properties of composite materials.

## Running the Application

The app is a Streamlit web interface. Run it from the `src/` directory:

```bash
cd src
streamlit run app.py
```

The Streamlit theme is configured in [src/.streamlit/config.toml](src/.streamlit/config.toml) (dark theme, orange accent).

## Installing Dependencies

```bash
pip install -r requirements.txt
```

Key libraries: `streamlit`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `pandas`, `Pillow`.

## Architecture

All source code lives under [src/](src/). The app is structured as a pipeline:

```
app.py → Homogenizacao → Micmodelos (micromechanical model) → DesenhoMecanico (plot)
```

### Core Classes

- **[src/analise/analise.py](src/analise/analise.py)** — `Analise`: Holds analysis configuration: `analise_type` (`'mecanica'` or `'condutividade'`), `geo` (geometry: `'esfera'`, `'cilindro'`, `'disco'`), and volume fractions (`fi`, `fm`, `fr`).

- **[src/materiais/materiais.py](src/materiais/materiais.py)** — `Materiais`: Base class for material phases. Stores phase identity (`id`), type, geometry, and volume fraction (`fk`).

- **[src/mecanico/mecanico.py](src/mecanico/mecanico.py)** — `Mecanico(Materiais)`: Mechanical material phase. Computes tensors L (stiffness), P (Hill), and S (Eshelby) from Young's modulus `E` and Poisson's ratio `v`.

- **[src/homogenizacao/homogenizacao.py](src/homogenizacao/homogenizacao.py)** — `Homogenizacao`: Orchestrator. Holds a list of material phases (`matH`), an `Analise` instance (`analH`), and a micromechanical model (`modH`). `calc()` distributes volume fractions and delegates to `modH.calc(self)`.

- **[src/micmodelos/micmodelos.py](src/micmodelos/micmodelos.py)** — `Micmodelos`: Abstract base class for micromechanical models. Each model implements `calc(objH)` taking a `Homogenizacao` instance.

- **[src/desenho/desenho_mec.py](src/desenho/desenho_mec.py)** — `DesenhoMecanico`: Generates plots by iterating over volume fractions and calling `objH.calc()`. Supports styles: `'fixar_fracao'` (E vs fi), `'poisson'` (Poisson ratio vs fi), `'normalizar'` (Eh/Em vs fi).

### Micromechanical Models (src/micmodelos/)

Each model extends `Micmodelos` and stores homogenized results (e.g., `Eh`, `vh`, `kh`, `Gh`):

| Model | File | Status |
|---|---|---|
| Voigt | [voigt.py](src/micmodelos/voigt.py) | Working |
| Reuss | [reuss.py](src/micmodelos/reuss.py) | Working |
| Dilute Suspension | [dilute.py](src/micmodelos/dilute.py) | Working |
| Mori-Tanaka | [moritanaka.py](src/micmodelos/moritanaka.py) | Working |
| Self-Consistent | [selfconsistent.py](src/micmodelos/selfconsistent.py) | Working |
| GSC | [gsc.py](src/micmodelos/gsc.py) | Working |
| Popovic | [popovic.py](src/micmodelos/popovic.py) | — |

Each model's `calc(objH)` reads from `objH.analH.analise_type` to dispatch between mechanical and conductivity analysis.

### Module Import Note

`app.py` imports modules using bare names (e.g., `from homogenizacao.homogenizacao import Homogenizacao`). Streamlit must be run from `src/` so Python resolves these relative to `src/`.

## Key Conventions

- Comments `# <------- FUNCIONANDO` mark tested/working code; `# <------- FALTA TESTAR` marks untested code.
- Volume fractions: `fi` = inclusion fraction, `fm` = matrix fraction, `fr` = reinforcement/third-phase fraction.
- Material phases in `matH`: index `[0]` = matrix, `[1]` = inclusion, `[2]` = third phase (if present).
- Tensors are 6×6 numpy arrays in Voigt notation.
- `analise_type` must match exactly: `'mecanica'` or `'condutividade'` (set via `Homogenizacao.set_analise()`).
