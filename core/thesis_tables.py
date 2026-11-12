"""Tables of the results section of the thesis (Coordination and Collaboration).

One function per sub-section of the results. They all work on the selected
benchmarks of the Analytics tab and compare, run by run, the federated search
with its twin search of client 0 (centralized), and with Popper on the whole
dataset. The hypothesis logs (every program of every round) are read from
artifacts/experiment_<id>/hypothesis_log.json, or from the database.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from database.connection import get_connection

ROOT = Path(__file__).resolve().parents[1]
DASH = "—"


# ----------------------------------------------------------------------
# Hypothesis logs
# ----------------------------------------------------------------------
def load_log(experiment_id: int) -> list[dict]:
    path = ROOT / "artifacts" / f"experiment_{experiment_id}" / "hypothesis_log.json"
    if path.is_file():
        try:
            entries = json.loads(path.read_text(encoding="utf-8"))
            return [e for e in entries if not e.get("is_final_validation")]
        except (OSError, ValueError):
            pass
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT sequence_number, hypothesis, score, epsilon_positive, epsilon_negative "
            "FROM hypothesis_log WHERE experiment_id = ? AND is_final_validation = 0 "
            "ORDER BY sequence_number",
            (int(experiment_id),),
        ).fetchall()
    return [dict(r) for r in rows]


def _key(text) -> tuple:
    return tuple(sorted(line.strip() for line in str(text).splitlines() if line.strip()))


def _split_top(text: str) -> list[str]:
    parts, depth, current = [], 0, ""
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += ch
    if current:
        parts.append(current)
    return parts


def solution_key(text) -> tuple:
    """A program up to spaces and to the order of the literals of each body (the
    bundled Popper and the centralized runner print the same program differently)."""
    rules = []
    for line in str(text).splitlines():
        line = "".join(line.split()).rstrip(".")
        if not line:
            continue
        head, _, body = line.partition(":-")
        rules.append((head, tuple(sorted(_split_top(body)))))
    return tuple(sorted(rules))


def _outcome(entry: dict) -> str:
    return f"{str(entry['epsilon_positive']).upper()} / {str(entry['epsilon_negative']).upper()}"


def first_difference(fed: list[dict], c0: list[dict]) -> int | None:
    """First round (1-based) at which the two searches differ: other program, or
    same program with another outcome or score. None if identical."""
    for i, (a, b) in enumerate(zip(fed, c0), start=1):
        if _key(a["hypothesis"]) != _key(b["hypothesis"]):
            return i
        if (a["epsilon_positive"], a["epsilon_negative"]) != (b["epsilon_positive"], b["epsilon_negative"]):
            return i
        if abs(float(a["score"]) - float(b["score"])) > 1e-9:
            return i
    if len(fed) != len(c0):
        return min(len(fed), len(c0)) + 1
    return None


# ----------------------------------------------------------------------
# Pairing of the runs
# ----------------------------------------------------------------------
def _pairs(runs: pd.DataFrame, benchmark_ids, approach: str):
    """Yield (benchmark_id, run_number, federated row, client-0 row or None,
    centralized-Popper row or None) for the selected federated benchmarks."""
    fed_all = runs[(runs["approach"] == approach) & (runs["benchmark_id"].isin(benchmark_ids))]
    for _, f in fed_all.sort_values(["benchmark_id", "run_number"]).iterrows():
        b = f["benchmark_id"]
        c0 = runs[(runs["approach"] == "central_testing") & (runs["baseline_of"] == b)
                  & (runs["run_number"] == f["run_number"])]
        cen = runs[(runs["approach"] == "centralized") & (runs["baseline_of"] == b)
                   & (runs["run_number"] == f["run_number"])]
        yield (int(b), int(f["run_number"]), f,
               c0.iloc[0] if not c0.empty else None,
               cen.iloc[0] if not cen.empty else None)


def _label(labels, b) -> str:
    return (labels or {}).get(int(b), f"#{int(b)}")


def _cell(values, digits=2) -> str:
    values = pd.Series(values, dtype="float").dropna()
    if values.empty:
        return DASH
    m = values.mean()
    return f"{m:.{digits}f} ± {values.std(ddof=0):.{digits}f}" if len(values) > 1 else f"{m:.{digits}f}"


# ----------------------------------------------------------------------
# 1. Equivalence with the centralized search
# ----------------------------------------------------------------------
def equivalence_rows(runs, benchmark_ids, approach, labels=None) -> pd.DataFrame:
    """One row per run pair, with the first round at which the searches differ."""
    rows = []
    for b, n, f, c0, cen in _pairs(runs, benchmark_ids, approach):
        if c0 is None:
            continue
        lf, lc = load_log(int(f["experiment_id"])), load_log(int(c0["experiment_id"]))
        diff = first_difference(lf, lc)
        same_cen = None
        if cen is not None and isinstance(cen["solution"], str) and isinstance(f["solution"], str):
            same_cen = solution_key(cen["solution"]) == solution_key(f["solution"])
        rows.append({
            "benchmark_id": b, "Benchmark": _label(labels, b), "dataset": f["dataset"],
            "k": int(f["k"]), "partition": f["partition_name"], "Run": n,
            "fed_experiment": int(f["experiment_id"]), "c0_experiment": int(c0["experiment_id"]),
            "Programs (federated)": len(lf), "Programs (client 0)": len(lc),
            "Equivalent": diff is None, "First difference": diff,
            "Same solution as client 0": (
                solution_key(f["solution"]) == solution_key(c0["solution"])
                if isinstance(f["solution"], str) and isinstance(c0["solution"], str) else None),
            "Same solution as Popper": same_cen,
        })
    return pd.DataFrame(rows)


def equivalence_table(runs, benchmark_ids, approach, labels=None) -> pd.DataFrame:
    detail = equivalence_rows(runs, benchmark_ids, approach, labels)
    if detail.empty:
        return detail
    out = []
    for b, g in detail.groupby("benchmark_id", sort=True):
        diffs = sorted(int(x) for x in g["First difference"].dropna())
        same_pop = g["Same solution as Popper"].dropna()
        out.append({
            "Benchmark": g.iloc[0]["Benchmark"],
            "Runs": len(g),
            "Equivalent runs": f"{int(g['Equivalent'].sum())}/{len(g)}",
            "First difference (round)": ", ".join(map(str, diffs)) if diffs else DASH,
            "Programs (federated)": _cell(g["Programs (federated)"], 0),
            "Programs (client 0)": _cell(g["Programs (client 0)"], 0),
            "Same solution as client 0": f"{int(g['Same solution as client 0'].fillna(False).sum())}/{len(g)}",
            "Same solution as Popper": (f"{int(same_pop.sum())}/{len(same_pop)}" if len(same_pop) else DASH),
        })
    return pd.DataFrame(out)


# ----------------------------------------------------------------------
# 2. Learned programs
# ----------------------------------------------------------------------
def programs_table(runs, benchmark_ids, approach, labels=None) -> pd.DataFrame:
    rows = []
    fed_all = runs[(runs["approach"] == approach) & (runs["benchmark_id"].isin(benchmark_ids))]
    for b, g in fed_all.groupby("benchmark_id", sort=True):
        c0 = runs[(runs["approach"] == "central_testing") & (runs["baseline_of"] == b)]
        cen = runs[(runs["approach"] == "centralized") & (runs["baseline_of"] == b)]
        for search, part in (("Federated", g), ("Client 0 (centralized)", c0), ("Popper (centralized)", cen)):
            if part.empty:
                continue
            solution = part["solution"].dropna()
            rows.append({
                "Benchmark": _label(labels, b), "Search": search, "Runs": len(part),
                "Rules": _cell(part["rules"], 1), "Body literals per rule": _cell(part["body_literals"], 2),
                "Program": solution.iloc[0].replace("\n", " ; ") if len(solution) else DASH,
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 3. Robustness to non-IID partitions: where the searches part
# ----------------------------------------------------------------------
def divergence_table(runs, benchmark_ids, approach, labels=None) -> pd.DataFrame:
    """For every run pair that is not equivalent: the round of divergence, with
    the answers of the clients, the aggregated answer and the answer of client 0."""
    rows = []
    for b, n, f, c0, _ in _pairs(runs, benchmark_ids, approach):
        if c0 is None:
            continue
        lf, lc = load_log(int(f["experiment_id"])), load_log(int(c0["experiment_id"]))
        d = first_difference(lf, lc)
        if d is None:
            continue
        a = lf[d - 1] if d - 1 < len(lf) else None
        c = lc[d - 1] if d - 1 < len(lc) else None
        same_prog = a is not None and c is not None and _key(a["hypothesis"]) == _key(c["hypothesis"])
        clients = ""
        if a is not None and a.get("client_outcomes"):
            clients = " ; ".join(
                f"C{o['client']}: {str(o['epsilon_positive']).upper()}/{str(o['epsilon_negative']).upper()} ({o['score']:g})"
                for o in a["client_outcomes"])
        rows.append({
            "Benchmark": _label(labels, b), "Run": n, "Round": d,
            "Cause": "same program, different answer" if same_prog else "different programs",
            "Program (federated)": (a["hypothesis"].replace("\n", " ; ") if a else DASH),
            "Clients": clients or DASH,
            "Aggregated": f"{_outcome(a)} ({float(a['score']):g})" if a else DASH,
            "Client 0": f"{_outcome(c)} ({float(c['score']):g})" if c else DASH,
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 4. Scalability: number of clients
# ----------------------------------------------------------------------
def scalability_table(runs, benchmark_ids, approach, labels=None) -> pd.DataFrame:
    detail = equivalence_rows(runs, benchmark_ids, approach, labels)
    if detail.empty:
        return detail
    rows = []
    fed_all = runs[(runs["approach"] == approach) & (runs["benchmark_id"].isin(benchmark_ids))]
    for (dataset, partition, k), g in fed_all.groupby(["dataset", "partition_name", "k"], sort=True):
        d = detail[(detail["dataset"] == dataset) & (detail["partition"] == partition) & (detail["k"] == k)]
        c0 = runs[(runs["approach"] == "central_testing") & (runs["baseline_of"].isin(g["benchmark_id"]))]
        rows.append({
            "Dataset": dataset, "Partition": partition, "Clients (K)": int(k), "Runs": len(g),
            "Equivalent runs": f"{int(d['Equivalent'].sum())}/{len(d)}" if len(d) else DASH,
            "Rounds": _cell(g["number_of_rounds"], 0),
            "Learning time (s)": _cell(g["learning_time_seconds_checked"]),
            "Client evaluation (s)": _cell(g["time_client_eval_checked"]),
            "Overhead (s)": _cell(g["time_overhead_checked"]),
            "Client 0: learning time (s)": _cell(c0["learning_time_seconds_checked"]),
            "Client 0: client evaluation (s)": _cell(c0["time_client_eval_checked"]),
            "Client 0: overhead (s)": _cell(c0["time_overhead_checked"]),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 0. Partition of the examples among the clients
# ----------------------------------------------------------------------
def partition_table(runs, benchmark_ids, approach, labels=None) -> pd.DataFrame:
    """Positive/negative examples held by each client, one row per selected
    benchmark (format of the tables of the thesis: "All", then Client 1..K).

    The runs of a benchmark share their seed, hence their partition; the table
    reads the first run of the benchmark and the column "Same in all runs" checks
    that the other runs have the same numbers.
    """
    fed_all = runs[(runs["approach"] == approach) & (runs["benchmark_id"].isin(benchmark_ids))]
    if fed_all.empty:
        return pd.DataFrame()
    rows, max_k = [], 0
    for b, g in fed_all.groupby("benchmark_id", sort=True):
        splits = []
        for _, f in g.sort_values("run_number").iterrows():
            with get_connection() as connection:
                found = connection.execute(
                    "SELECT client_id, number_of_positive_examples AS pos, "
                    "number_of_negative_examples AS neg FROM client_results "
                    "WHERE experiment_id = ? ORDER BY client_id",
                    (int(f["experiment_id"]),),
                ).fetchall()
            if found:
                splits.append([(int(r["pos"]), int(r["neg"])) for r in found])
        if not splits:
            continue
        first = splits[0]
        total_pos = sum(p for p, _ in first)
        total_neg = sum(n for _, n in first)
        row = {
            "Benchmark": _label(labels, b),
            "Dataset": g.iloc[0]["dataset"],
            "Partition": g.iloc[0]["partition_name"],
            "Clients (K)": len(first),
            "All": f"{total_pos}/{total_neg}",
        }
        for i, (p, n) in enumerate(first, start=1):
            row[f"Client {i}"] = f"{p}/{n}"
        row["Same in all runs"] = "yes" if all(s == first for s in splits) else "no"
        max_k = max(max_k, len(first))
        rows.append(row)
    frame = pd.DataFrame(rows)
    # Benchmarks with fewer clients leave the extra client columns empty.
    for i in range(1, max_k + 1):
        if f"Client {i}" not in frame:
            frame[f"Client {i}"] = DASH
        frame[f"Client {i}"] = frame[f"Client {i}"].fillna(DASH)
    fixed = ["Benchmark", "Dataset", "Partition", "Clients (K)", "All"]
    clients = [f"Client {i}" for i in range(1, max_k + 1)]
    return frame[fixed + clients + ["Same in all runs"]]


# ----------------------------------------------------------------------
# 6. Communication
# ----------------------------------------------------------------------
def communication_table(runs, benchmark_ids, approach, labels=None) -> pd.DataFrame:
    """Messages sent by the clients, counted from the hypothesis log: for each
    program and each client, one answer (outcome and score) and, for each clause
    of the program, one clause-level answer (two booleans). No byte count."""
    rows = []
    fed_all = runs[(runs["approach"] == approach) & (runs["benchmark_id"].isin(benchmark_ids))]
    for b, g in fed_all.groupby("benchmark_id", sort=True):
        counts = []
        for _, f in g.iterrows():
            log = load_log(int(f["experiment_id"]))
            k = int(f["k"])
            clauses = sum(len([l for l in str(e["hypothesis"]).splitlines() if l.strip()]) for e in log)
            counts.append((len(log), k * len(log), k * clauses))
        if not counts:
            continue
        rows.append({
            "Benchmark": _label(labels, b), "Clients (K)": int(g.iloc[0]["k"]),
            "Programs sent by the server": _cell([c[0] for c in counts], 0),
            "Answers per client": _cell([c[0] for c in counts], 0),
            "Outcome answers (all clients)": _cell([c[1] for c in counts], 0),
            "Clause answers (all clients)": _cell([c[2] for c in counts], 0),
        })
    return pd.DataFrame(rows)
