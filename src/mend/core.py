import numpy as np


def feasible(agreement):
    z = np.asarray(agreement["contract"], float)
    if abs(z.sum()) > 1e-8:
        return False
    if not agreement["physical_feasible"]:
        return False
    if "A" in agreement and np.any(
        np.asarray(agreement["A"]) @ z > np.asarray(agreement["b"]) + 1e-8
    ):
        return False
    if "E" in agreement and not np.allclose(
        np.asarray(agreement["E"]) @ z, agreement["e"], atol=1e-8
    ):
        return False
    return True


def score(y, c, endpoint):
    values = np.maximum(np.asarray(y[endpoint], float), 0)
    weights = np.asarray(y.get("weights", np.ones(len(values))), float)
    return float(
        np.sum(weights * np.log(c["delta"] + values))
        - c["risk_weight"] * y["risk"]
        - c["cost_weight"] * y["cost"]
    )


def select(menu, c, method, rng):
    valid = [y for y in menu if feasible(y)]
    query = set()
    representatives = []
    if method == "mend":
        for schedule in sorted({y["schedule"] for y in valid}):
            candidates = [y for y in valid if y["schedule"] == schedule]
            for cost in sorted({y["cost"] for y in candidates}):
                level = [y for y in candidates if y["cost"] == cost]
                query.update(y["id"] for y in level)
                acceptable = [y for y in level if min(y["lower"]) >= 0]
                if acceptable:
                    representatives.append(
                        max(acceptable, key=lambda y: (score(y, c, "lower"), y["id"]))
                    )
                    break
    else:
        query.update(y["id"] for y in valid)
        representatives = [
            y
            for y in valid
            if min(
                y["lower"]
                if method in ("robust_nash", "random", "uniform")
                else y["point"]
            )
            >= 0
        ]
    if not representatives:
        return None, dict(queried=sorted(query), certified=False, certificate_gap=None)
    if method == "random":
        chosen = representatives[int(rng.integers(len(representatives)))]
    elif method == "uniform":
        chosen = min(
            representatives, key=lambda y: (np.var(y["contract"]), y["cost"], y["id"])
        )
    elif method == "risk_first":
        chosen = min(representatives, key=lambda y: (y["risk"], y["cost"], y["id"]))
    else:
        chosen = max(
            representatives,
            key=lambda y: (
                score(y, c, "lower" if method in ("mend", "robust_nash") else "point"),
                y["id"],
            ),
        )
    others = [y for y in valid if y["id"] != chosen["id"]]
    gap = score(chosen, c, "lower") - max(
        (score(y, c, "upper") for y in others), default=-np.inf
    )
    query.update(y["id"] for y in others)
    return chosen, dict(
        queried=sorted(query), certificate_gap=gap, certified=bool(gap > 0)
    )


def negotiate(menu, private, c, method, rng):
    pool = list(menu)
    trace = []
    queried = set()
    for _ in range(len(menu)):
        proposal, certificate = select(pool, c, method, rng)
        queried.update(certificate["queried"])
        if proposal is None:
            break
        surplus = np.asarray(private[proposal["id"]], float)
        consent = (surplus >= 0).tolist()
        trace.append(dict(id=proposal["id"], consent=consent, certificate=certificate))
        if all(consent):
            return proposal, trace, queried
        pool = [y for y in pool if y["id"] != proposal["id"]]
    return None, trace, queried
