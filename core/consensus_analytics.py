"""Data for the Consensus tab of the Analytics page.

Pure functions (no Streamlit): they read the benchmarks recorded in the
database and the per-run files written by the Consensus server
(`artifacts/experiment_<id>/consensus/`), and return pandas objects.

Baseline: the platform's "centralized" approach is scored on its own
training data, so it cannot be compared with the Consensus test accuracy.
The fair baseline is a Consensus run with ONE client: the same learner on
the whole training set, scored on the same test set (the split depends only
on the dataset and the seed).
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

from database.connection import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[1]

BASELINE_LABEL = "Centralized (1 client)"
METRICS = ("accuracy", "precision", "recall", "f1", "mcc")


# ---------------------------------------------------------------------
# Reading the runs
# ---------------------------------------------------------------------

def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def rule_statistics(hypothesis: list[str]) -> tuple[int, float]:
    """(number of rules, mean number of body literals per rule)."""
    rules = [rule for rule in hypothesis if rule and rule.strip()]
    if not rules:
        return 0, 0.0
    lengths = []
    for rule in rules:
        body = rule.split(":-", 1)[1] if ":-" in rule else ""
        lengths.append(len(re.findall(r"[a-z_][A-Za-z0-9_]*\(", body)))
    return len(rules), float(np.mean(lengths))


def load_consensus_runs() -> pd.DataFrame:
    """One row per completed Consensus run."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                b.id AS benchmark_id, b.name AS benchmark_name,
                b.dataset, b.learner, b.number_of_clients AS k,
                b.partition_strategy AS partition, b.base_seed,
                br.run_number, br.experiment_id
            FROM benchmarks AS b
            JOIN benchmark_runs AS br ON br.benchmark_id = b.id
            JOIN experiments AS e ON e.id = br.experiment_id
            WHERE b.approach = 'consensus' AND e.status = 'COMPLETED'
            ORDER BY b.id, br.run_number
            """
        ).fetchall()

        # Centralized baselines launched "on the same data" from the
        # Experiments page: consensus experiment id -> baseline experiment id.
        links = {
            int(r["reference_experiment_id"]): int(r["id"])
            for r in connection.execute(
                "SELECT id, reference_experiment_id FROM experiments "
                "WHERE approach = 'centralized' AND status = 'COMPLETED' "
                "AND reference_experiment_id IS NOT NULL ORDER BY id"
            ).fetchall()
        }

    records = []
    for row in rows:
        run = dict(row)
        folder = (
            PROJECT_ROOT / "artifacts" / f"experiment_{run['experiment_id']}" / "consensus"
        )
        analysis = _read_json(folder / "consensus_analysis.json") or {}
        server = _read_json(folder / "server_result.json") or {}
        consensus = analysis.get("consensus")
        if not consensus:
            continue

        per_hypothesis = analysis.get("per_hypothesis", {})
        hypotheses = server.get("hypotheses", [])
        stats = [rule_statistics(h) for h in hypotheses]
        times = [float(v) for v in (analysis.get("induction_time_per_client") or {}).values()]
        communication = analysis.get("communication") or {}
        margins = analysis.get("margin_distribution") or {}
        total_examples = sum(margins.values()) if margins else 0
        decided_by_one = analysis.get("examples_decided_by_one_vote")

        record = {
            "benchmark_id": run["benchmark_id"],
            "benchmark": run["benchmark_name"],
            "run_number": run["run_number"],
            "experiment_id": run["experiment_id"],
            "dataset": run["dataset"],
            "learner": run["learner"] or "popper",
            "k": int(run["k"]),
            "partition": run["partition"],
            "seed": int(run["base_seed"] or 0) + int(run["run_number"]) - 1,
            "n_test": int(consensus["tp"] + consensus["fp"] + consensus["tn"] + consensus["fn"]),
            "n_test_pos": int(consensus["tp"] + consensus["fn"]),
            "n_test_neg": int(consensus["tn"] + consensus["fp"]),
            # Accuracy of always predicting the most frequent class of the test set.
            "majority_class": (
                max(consensus["tp"] + consensus["fn"], consensus["tn"] + consensus["fp"])
                / (consensus["tp"] + consensus["fp"] + consensus["tn"] + consensus["fn"])
                if (consensus["tp"] + consensus["fp"] + consensus["tn"] + consensus["fn"])
                else float("nan")
            ),
            "n_empty": sum(1 for count, _ in stats if count == 0),
            "rules_total": sum(count for count, _ in stats),
            "rules_per_hypothesis": float(np.mean([c for c, _ in stats])) if stats else 0.0,
            "body_literals": (
                float(np.mean([length for count, length in stats if count]))
                if any(count for count, _ in stats)
                else 0.0
            ),
            "time_slowest": max(times) if times else float("nan"),
            "time_mean": float(np.mean(times)) if times else float("nan"),
            "upload_kb": (
                sum((communication.get("upload_bytes_per_client") or {}).values()) / 1024
                if communication
                else float("nan")
            ),
            "ensemble_kb": (
                float(communication.get("ensemble_bytes", 0.0)) / 1024
                if communication
                else float("nan")
            ),
            "round_seconds": analysis.get("federated_round_seconds", float("nan")),
            "one_vote_share": (
                (decided_by_one / total_examples)
                if (decided_by_one is not None and total_examples)
                else float("nan")
            ),
        }
        # Linked centralized baseline (same data, same split).
        baseline = None
        if run["experiment_id"] in links:
            baseline_folder = (
                PROJECT_ROOT / "artifacts"
                / f"experiment_{links[run['experiment_id']]}" / "consensus"
            )
            baseline = (_read_json(baseline_folder / "consensus_analysis.json") or {})
            baseline_hyp = (_read_json(baseline_folder / "server_result.json") or {}).get("hypotheses", [[]])
        for metric in METRICS:
            record[f"baseline_{metric}"] = (
                float(baseline["consensus"].get(metric, 0.0))
                if baseline and baseline.get("consensus")
                else float("nan")
            )
        if baseline and baseline.get("consensus"):
            base_times = list((baseline.get("induction_time_per_client") or {}).values())
            record["baseline_time"] = float(base_times[0]) if base_times else float("nan")
            base_rules = rule_statistics(baseline_hyp[0] if baseline_hyp else [])
            record["baseline_rules"], record["baseline_body"] = base_rules
        else:
            record["baseline_time"] = float("nan")
            record["baseline_rules"] = float("nan")
            record["baseline_body"] = float("nan")
        for metric in METRICS:
            record[f"consensus_{metric}"] = float(consensus.get(metric, 0.0))
            values = [float(h.get(metric, 0.0)) for h in per_hypothesis.values()]
            record[f"mean_h_{metric}"] = float(np.mean(values)) if values else float("nan")
            record[f"best_h_{metric}"] = float(np.max(values)) if values else float("nan")
            record[f"worst_h_{metric}"] = float(np.min(values)) if values else float("nan")
        records.append(record)

    frame = pd.DataFrame(records)
    if not frame.empty:
        frame["setting"] = np.where(
            frame["k"] == 1,
            BASELINE_LABEL,
            "k=" + frame["k"].astype(str) + ", " + frame["partition"].astype(str),
        )
    return frame


def load_partitions(runs: pd.DataFrame) -> pd.DataFrame:
    """Positive / negative examples held by each client, and in the common
    test set, for every run in `runs` (one row per run and part)."""
    if runs.empty:
        return pd.DataFrame()

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT experiment_id, client_id, number_of_positive_examples AS pos, "
            "number_of_negative_examples AS neg FROM client_results "
            f"WHERE experiment_id IN ({','.join('?' * len(runs))})",
            [int(i) for i in runs["experiment_id"]],
        ).fetchall()
    clients = pd.DataFrame([dict(r) for r in rows])

    records = []
    for _, run in runs.iterrows():
        mine = clients[clients["experiment_id"] == run["experiment_id"]] if not clients.empty else clients
        for _, row in mine.sort_values("client_id").iterrows():
            records.append(
                {
                    "experiment_id": run["experiment_id"],
                    "part": f"Client {int(row['client_id'])}",
                    "order": int(row["client_id"]),
                    "pos": int(row["pos"] or 0),
                    "neg": int(row["neg"] or 0),
                }
            )
        records.append(
            {
                "experiment_id": run["experiment_id"],
                "part": "Test (common)",
                "order": 10**6,
                "pos": int(run["n_test_pos"]),
                "neg": int(run["n_test_neg"]),
            }
        )
    return pd.DataFrame(records)


def keep_one_run_per_seed(runs: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Runs launched again with the same dataset, learner, number of clients,
    partition and seed use the very same split, hence give the same result:
    they are repeats, not independent runs. Counting them would shrink the
    error bars and fake a large number of runs. For each such group, keep the
    run that has a linked centralized baseline, then the most recent one.
    Returns the kept runs and the number of runs dropped."""
    if runs.empty:
        return runs, 0
    ranked = runs.assign(_has_baseline=runs["baseline_accuracy"].notna()).sort_values(
        ["_has_baseline", "experiment_id"], ascending=[False, False]
    )
    kept = ranked.drop_duplicates(
        ["dataset", "learner", "k", "partition", "seed"], keep="first"
    ).drop(columns="_has_baseline")
    return kept.sort_values(["dataset", "learner", "k", "partition", "seed"]).reset_index(drop=True), len(runs) - len(kept)


def load_vote_traces(experiment_id: int) -> list[dict]:
    path = (
        PROJECT_ROOT / "artifacts" / f"experiment_{experiment_id}" / "consensus" / "vote_traces.json"
    )
    return _read_json(path) or []


# ---------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------

def mean_and_se(values) -> tuple[float, float]:
    values = np.asarray([v for v in values if v == v], dtype=float)
    if values.size == 0:
        return float("nan"), float("nan")
    if values.size == 1:
        return float(values[0]), 0.0
    return float(values.mean()), float(values.std(ddof=1) / math.sqrt(values.size))


def paired_p_value(first, second) -> float:
    """Two-sided paired t-test p-value, NaN when it cannot be computed."""
    first = np.asarray(first, dtype=float)
    second = np.asarray(second, dtype=float)
    mask = ~(np.isnan(first) | np.isnan(second))
    differences = (first - second)[mask]
    if differences.size < 3:
        return float("nan")
    spread = differences.std(ddof=1)
    if spread == 0:
        return 1.0 if differences.mean() == 0 else 0.0
    t_statistic = differences.mean() / (spread / math.sqrt(differences.size))
    try:
        from scipy import stats as scipy_stats

        return float(2 * scipy_stats.t.sf(abs(t_statistic), differences.size - 1))
    except ImportError:
        # SciPy is not installed: exact two-sided p-value of Student's t
        # distribution (the normal approximation is far too optimistic with
        # only a handful of runs).
        return _student_two_sided_p(abs(t_statistic), differences.size - 1)


def _student_two_sided_p(t: float, dof: int) -> float:
    """Two-sided p-value of Student's t distribution, without SciPy:
    p = I_x(dof/2, 1/2) with x = dof / (dof + t^2) (regularized incomplete beta)."""
    x = dof / (dof + t * t)
    a, b = dof / 2.0, 0.5

    def beta_continued_fraction(x, a, b):
        tiny = 1e-300
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c, d = 1.0, 1.0 - qab * x / qap
        d = 1.0 / (d if abs(d) > tiny else tiny)
        h = d
        for m in range(1, 300):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1.0 + aa * d
            d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1.0 + aa * d
            d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            delta = d * c
            h *= delta
            if abs(delta - 1.0) < 1e-12:
                break
        return h

    log_front = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x)
    ) if 0.0 < x < 1.0 else None
    if log_front is None:
        return 1.0 if x >= 1.0 else 0.0
    front = math.exp(log_front)
    if x < (a + 1.0) / (a + b + 2.0):
        return float(front * beta_continued_fraction(x, a, b) / a)
    return float(1.0 - front * beta_continued_fraction(1.0 - x, b, a) / b)


def summary_table(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    """One row per dataset and setting, mean ± SE over seeds. The centralized
    column comes from the baseline linked to each consensus run (same data,
    same split); the p-value is a paired t-test over those runs."""
    rows = []
    for (dataset, learner), group in frame.groupby(["dataset", "learner"]):
        for setting, subset in group.groupby("setting"):
            consensus_mean, consensus_se = mean_and_se(subset[f"consensus_{metric}"])
            member_mean, member_se = mean_and_se(subset[f"mean_h_{metric}"])
            best_mean, best_se = mean_and_se(subset[f"best_h_{metric}"])
            row = {
                "Dataset": dataset,
                "Learner": learner,
                "Setting": setting,
                "Runs": len(subset),
                "Test examples": int(subset["n_test"].iloc[0]),
                "Majority class": (
                    f"{subset['majority_class'].mean():.3f}"
                    if metric == "accuracy"
                    else "0.000" if metric == "mcc" else "—"
                ),
                "Consensus": f"{consensus_mean:.3f} ± {consensus_se:.3f}",
                "Average client (alone)": f"{member_mean:.3f} ± {member_se:.3f}",
                "Best client (alone)": f"{best_mean:.3f} ± {best_se:.3f}",
                "Centralized (same split)": "—",
                "p (consensus vs centralized)": float("nan"),
            }
            linked = subset[subset[f"baseline_{metric}"].notna()]
            if not linked.empty:
                base_mean, base_se = mean_and_se(linked[f"baseline_{metric}"])
                row["Centralized (same split)"] = f"{base_mean:.3f} ± {base_se:.3f}"
                row["p (consensus vs centralized)"] = paired_p_value(
                    linked[f"consensus_{metric}"], linked[f"baseline_{metric}"]
                )
            rows.append(row)
    return pd.DataFrame(rows)


def cost_table(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per dataset and setting: size of the learned theories, learning
    time and communication, consensus next to the centralized baseline
    (mean ± SE over seeds). Rules and literals are per hypothesis; the
    consensus time is that of the slowest client (clients learn in parallel)."""

    def cell(values, digits=2) -> str:
        mean, se = mean_and_se(values)
        if mean != mean:
            return "—"
        return f"{mean:.{digits}f} ± {se:.{digits}f}"

    rows = []
    for (dataset, learner), group in frame.groupby(["dataset", "learner"]):
        for setting, subset in group.groupby("setting"):
            linked = subset[subset["baseline_accuracy"].notna()]
            rows.append(
                {
                    "Dataset": dataset,
                    "Learner": learner,
                    "Setting": setting,
                    "Runs": len(subset),
                    "Rules (consensus)": cell(subset["rules_per_hypothesis"], 1),
                    "Rules (centralized)": cell(linked["baseline_rules"], 1),
                    "Literals (consensus)": cell(subset["body_literals"]),
                    "Literals (centralized)": cell(linked["baseline_body"]),
                    "Time s (consensus)": cell(subset["time_slowest"], 1),
                    "Time s (centralized)": cell(linked["baseline_time"], 1),
                    "Upload KB (consensus)": cell(subset["upload_kb"]),
                }
            )
    return pd.DataFrame(rows)


def to_latex(table: pd.DataFrame, caption: str, label: str) -> str:
    """Small booktabs table, escaped for LaTeX."""
    def escape(value) -> str:
        text = "" if value is None else str(value)
        text = text.replace("±", r"$\pm$")
        for source, target in (("_", r"\_"), ("%", r"\%"), ("&", r"\&"), ("#", r"\#")):
            text = text.replace(source, target)
        return "nan" if text == "nan" else text

    columns = list(table.columns)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        r"\begin{tabular}{" + "l" * len(columns) + "}",
        r"\toprule",
        " & ".join(escape(c) for c in columns) + r" \\",
        r"\midrule",
    ]
    for _, row in table.iterrows():
        cells = []
        for value in row:
            if isinstance(value, float):
                cells.append("--" if value != value else f"{value:.3f}")
            else:
                cells.append(escape(value))
        lines.append(" & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Agreement between the hypotheses of one run
# ---------------------------------------------------------------------

def agreement_matrix(traces: list[dict]) -> pd.DataFrame:
    """Share of test examples on which two hypotheses give the same answer;
    the 'Truth' row/column gives each hypothesis' accuracy."""
    if not traces:
        return pd.DataFrame()
    names = [vote["hypothesis"] for vote in traces[0]["votes"]]
    labels = names + ["Truth", "Consensus"]
    answers = {name: [] for name in labels}
    for trace in traces:
        for vote in trace["votes"]:
            answers[vote["hypothesis"]].append(vote["prediction"] == "POS")
        answers["Truth"].append(trace["true_label"] == "POS")
        answers["Consensus"].append(trace["prediction"] == "POS")
    matrix = pd.DataFrame(index=labels, columns=labels, dtype=float)
    for first in labels:
        for second in labels:
            matrix.loc[first, second] = float(
                np.mean(np.array(answers[first]) == np.array(answers[second]))
            )
    return matrix
