# MEND

Implementation of limited-disclosure bargaining over executable schedule–contract agreements.

## Installation

Use Python `>=3.11`. Run commands from the repository root. Create the environment, activate it with `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\Activate.ps1` (PowerShell), then install the package.

```bash
python -m venv .venv
```

```bash
python -m pip install -e .
```

## Data preparation

Preparation generates finite schedule/contract menus and separates public cases from private consent/evaluation surplus. To import agreements, add `--input agreements.json` with `id`, `source`, `menu` and `private`; menu entries retain executable schedules, budget-balanced transfers, public feasibility and surplus bounds.

```bash
mend prepare --config configs/reproduce.json --data data/menu
```

## Execution

`configs/reproduce.json` fixes seed `17`. Keep this config for every step; change `seed` there and use separate data/output directories for independent runs.

```bash
mend run --config configs/reproduce.json --data data/menu --output runs
```

## Evaluation and comparisons

`compare` executes the available methods, including component controls, on the same prepared inputs.

```bash
mend compare --config configs/reproduce.json --data data/menu --output runs
mend plot --output runs
```

## Outputs

`runs/<method>/` contains `episodes.csv`, `traces.json` and `metrics.json`. Comparisons write `runs/comparison.csv` and `runs/comparison.json`; plots go to `runs/figures/`.

## Verification

Source checks used Python 3.13.5. Installed dependency metadata: numpy 2.1.3, scipy 1.15.3, matplotlib 3.10.0. Python AST, configuration files, CLI parser definitions and source input/output paths were checked without invoking command handlers. Training, full evaluation and CI were not run for this review.
