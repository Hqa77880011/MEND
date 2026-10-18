# MEND

Implementation of limited-disclosure bargaining over executable schedule–contract agreements.

## Installation


Use Python 3.11 or newer. Create and activate a virtual environment, then install:

```bash
python -m venv .venv
```

Activate with `source .venv/bin/activate` on Linux/macOS or `.venv\Scripts\Activate.ps1` in PowerShell, then install:

```bash
python -m pip install -e .
``` For GPU execution, install matching PyTorch and torchvision builds using the [PyTorch selector](https://pytorch.org/get-started/locally/).


## Prepare agreements

MEND consumes finite public contract menus. `mend prepare --input agreements.json` separates each episode into public interval reports and private consent/evaluation surpluses. The input is a JSON list of `{id, source, menu, private}`. Each menu entry has `id`, `schedule`, `contract` (a budget-balanced transfer vector), nonnegative `cost`, public `risk`, `physical_feasible`, `point`, `lower`, `upper`. Optional `A,b,E,e` impose linear contract inequalities/equalities. `private` maps agreement IDs to realized surplus vectors relative to disagreement. Use distinct episode IDs. Intervals must be calibrated using held-out physical scenarios before constructing test menus.

Physical scenarios can come from [CityLearn](https://www.citylearn.net/), [NASA battery aging](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/) and [MATPOWER cases](https://matpower.org/). These sources do not contain private bargaining utilities. Evaluate feeder/crew/reserve feasibility with your physical oracle and write its result to `physical_feasible`; the bargaining solver checks executable transfer constraints itself. This finite-menu implementation leaves power flow and utility estimation upstream. A generated menu workload is available by omitting `--input`; its source is recorded as generated and its numbers describe that workload.

```bash
mend prepare --data data/menu
mend run --data data/menu --method mend --output runs
mend compare --data data/menu --output runs
mend plot --output runs
```

## Selection and comparisons

For each schedule, increasing cost levels are queried until the first robustly acceptable level. The lowest-cost package wins, breaking ties by lower-confidence Nash score. Schedule representatives maximize the lower score minus public risk and concession penalties. A positive ranking certificate requires the chosen lower score to exceed every other feasible agreement's upper score. Upper-bound queries are counted. Operators retain unanimous consent; rejected proposals leave the no-repeat pool. Private realized surplus is exposed only to local consent and final evaluation, not selection.

Comparison methods are robust Nash without contraction, point Nash, risk-first, random and most-uniform transfer. They share menus and feasibility. `configs/default.json` sets seed, generated workload size, interval width, binding-conflict fraction, Nash stabilizer `delta` and score penalty weights. Change conflict fraction and package coupling in input menus for the binding/nonbinding controls. No learned bargaining parameter is required.

## Results

Each method writes `episodes.csv`, `traces.json` and `metrics.json` under `runs/METHOD`. Outputs include agreement rate, cost conditional on agreement, social welfare and its ratio to the full-information maximum-sum feasible individually rational reference, worst-agent **absolute surplus** regret, IR violations, certificate coverage and actual serialized report/proposal KB. The full-information comparator uses the same finite menu; it is an evaluation reference rather than a deployable selector. Communication includes public feasibility metadata in transmitted entries. These explicit conventions replace unspecified physical-oracle, private-utility and normalization details. Comparison CSV/JSON and PNG/SVG plots contain only computed measurements. All no-agreement episodes retain zero disagreement surplus.

## Registered compact reproduction setting

Four-operator finite schedule/contract menus with known generated surplus intervals and a public linear feasibility oracle. Scores describe this contract game; no feeder measurements are assumed.

Run from the repository root after installation. The following commands use the registered setting; they are provided for execution and have not been run as part of the source review.

```bash
mend prepare --config configs/reproduce.json --data data/reproduce
mend compare --config configs/reproduce.json --data data/reproduce --output runs/reproduce
```

This setting needs no external dataset or pretrained weights. Generated inputs and declared fault/shift laws define the finite task; reported quantities retain that provenance.

## Multiple seeds

Run matched configurations with different seeds in separate directories, then aggregate the generated metric files:

```bash
mend-report --inputs runs/seed0/metrics.json runs/seed1/metrics.json --output outputs/seeds
```

Use actual metric paths from your runs, including method subdirectories where applicable. Keep dataset, split and experimental condition fixed within a report. Summary CSV/JSON gives per-method arithmetic means and sample standard deviations; a single run has no standard-deviation estimate.
