import argparse
from pathlib import Path
import numpy as np
from .common import load, save, table, plot
from .core import feasible, negotiate


def prepare(c, output, input_path):
    if input_path:
        cases = load(input_path)
    else:
        rng = np.random.default_rng(c["seed"])
        cases = []
        for episode in range(c["episodes"]):
            menu = []
            private = {}
            binding = rng.random() < c["conflict"]
            for plan in range(c["schedules"]):
                base = rng.uniform(0.05, 1, c["agents"])
                if binding:
                    base[int(rng.integers(c["agents"]))] = -rng.uniform(0.05, 0.4)
                for package in range(c["packages"]):
                    transfer = (
                        rng.normal(0, 0.2, c["agents"])
                        if package
                        else np.zeros(c["agents"])
                    )
                    transfer -= transfer.mean()
                    truth = base + transfer
                    identity = f"{plan}:{package}"
                    point = truth + rng.normal(0, c["interval_width"] / 3, c["agents"])
                    menu.append(
                        dict(
                            id=identity,
                            schedule=str(plan),
                            contract=transfer.tolist(),
                            cost=float(np.abs(transfer).sum() / 2),
                            risk=float(max(0, -base.min())),
                            physical_feasible=bool(np.abs(transfer).max() < 0.5),
                            A=np.r_[np.eye(c["agents"]), -np.eye(c["agents"])].tolist(),
                            b=[0.5] * (2 * c["agents"]),
                            point=point.tolist(),
                            lower=(point - c["interval_width"]).tolist(),
                            upper=(point + c["interval_width"]).tolist(),
                        )
                    )
                    private[identity] = truth.tolist()
            cases.append(
                dict(
                    id=str(episode),
                    source="generated_finite_contract_menu",
                    menu=menu,
                    private=private,
                )
            )
    public = []
    private = []
    for case in cases:
        if not case["menu"] or len({y["id"] for y in case["menu"]}) != len(
            case["menu"]
        ):
            raise ValueError("Menu IDs must be nonempty and unique")
        for y in case["menu"]:
            if np.any(np.asarray(y["lower"]) > np.asarray(y["upper"])):
                raise ValueError("Invalid interval")
        public.append({k: v for k, v in case.items() if k != "private"})
        private.append(dict(id=case["id"], surplus=case["private"]))
    save(Path(output) / "cases.json", public)
    save(Path(output) / "private.json", private)


def run(a, c, method):
    cases = load(Path(a.data) / "cases.json")
    private = {r["id"]: r["surplus"] for r in load(Path(a.data) / "private.json")}
    rows = []
    traces = []
    rng = np.random.default_rng(c["seed"])
    for case in cases:
        secret = private[case["id"]]
        menu = case["menu"]
        oracle = [y for y in menu if feasible(y) and min(secret[y["id"]]) >= 0]
        optimum = max(oracle, key=lambda y: sum(secret[y["id"]]), default=None)
        selected, trace, queries = negotiate(menu, secret, c, method, rng)
        truth = (
            np.array(secret[selected["id"]])
            if selected
            else np.zeros(len(menu[0]["lower"]))
        )
        best = (
            np.max([secret[y["id"]] for y in oracle], axis=0)
            if oracle
            else np.zeros(len(truth))
        )
        report = dict(
            id=case["id"],
            method=method,
            agreement=selected is not None,
            concession_cost=selected["cost"] if selected else None,
            welfare=float(truth.sum()),
            normalized_welfare=float(truth.sum() / sum(secret[optimum["id"]]))
            if optimum and sum(secret[optimum["id"]]) > 0
            else None,
            worst_agent_regret=float(np.max(best - truth)),
            ir_violation=bool(np.any(truth < 0)),
            traffic_kb=len(
                __import__("json")
                .dumps(
                    dict(
                        intervals=[y for y in menu if y["id"] in queries],
                        proposals=trace,
                    )
                )
                .encode()
            )
            / 1000,
            proposals=len(trace),
            certified=bool(trace and trace[-1]["certificate"]["certified"]),
        )
        rows.append(report)
        traces.append(dict(id=case["id"], proposals=trace))
    output = Path(a.output) / method
    table(output / "episodes.csv", rows)
    summary = {"method": method}
    for key in [
        "agreement",
        "concession_cost",
        "welfare",
        "normalized_welfare",
        "worst_agent_regret",
        "ir_violation",
        "traffic_kb",
        "certified",
    ]:
        values = [r[key] for r in rows if r[key] is not None]
        summary[key] = float(np.mean(values)) if values else None
    save(output / "metrics.json", summary)
    save(output / "traces.json", traces)
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["prepare", "run", "compare", "plot"])
    p.add_argument("--config", default="configs/default.json")
    p.add_argument("--input")
    p.add_argument("--data", default="data/menu")
    p.add_argument("--output", default="runs")
    p.add_argument(
        "--method",
        choices=[
            "mend",
            "robust_nash",
            "point_nash",
            "risk_first",
            "random",
            "uniform",
        ],
        default="mend",
    )
    a = p.parse_args()
    c = load(a.config)
    if a.command == "prepare":
        prepare(c, a.data, a.input)
    elif a.command == "run":
        run(a, c, a.method)
    elif a.command == "compare":
        rows = [
            run(a, c, m)
            for m in [
                "mend",
                "robust_nash",
                "point_nash",
                "risk_first",
                "random",
                "uniform",
            ]
        ]
        save(Path(a.output) / "comparison.json", rows)
        table(Path(a.output) / "comparison.csv", rows)
    else:
        plot(Path(a.output) / "comparison.json", Path(a.output) / "figures")
