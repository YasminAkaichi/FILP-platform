"""Tables of the hybrid evaluation protocol (federated search vs client 0).

For every federated benchmark of Coordination / Collaboration that has a
"Centralized testing" twin (same dataset, same seeds), this script prints and
writes (results_tables/):

  hybrid_performance.csv / .tex   mean +- std of rounds, programs and times of
                                  the two searches (one row per setting and search)
  hybrid_equivalence.csv / .tex   run by run: do the two searches generate the
                                  same programs? first round where they differ

Usage:  python scripts/hybrid_results.py [--db data/filp_platform.db]
                                         [--approach coordination|collaboration]
                                         [--benchmarks 269 275 ...]
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results_tables"


def connect(path: str) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def pairs(c, approaches, only):
    """(federated benchmark, twin benchmark) for every complete setting."""
    rows = c.execute(
        "select * from benchmarks where approach in (%s) and status='COMPLETED' order by id"
        % ",".join("?" * len(approaches)), approaches).fetchall()
    out = []
    for f in rows:
        if f["name"].startswith("Centralized testing"):
            continue
        if only and f["id"] not in only:
            continue
        twin = next((t for t in rows if t["id"] > f["id"]
                     and t["name"].startswith("Centralized testing")
                     and t["approach"] == f["approach"] and t["dataset"] == f["dataset"]), None)
        if twin:
            out.append((f, twin))
    return out


def run_ids(c, benchmark_id):
    return {r["run_number"]: r["experiment_id"] for r in c.execute(
        "select run_number, experiment_id from benchmark_runs where benchmark_id=?", (benchmark_id,))}


def metrics(c, exp):
    s = c.execute("select * from server_results where experiment_id=?", (exp,)).fetchone()
    if s is None:
        return None
    ev = c.execute("select max(total_eval_wall_seconds) m from client_results where experiment_id=?",
                   (exp,)).fetchone()["m"] or 0.0
    return {
        "found": bool(s["solution_found"]), "rounds": s["number_of_rounds"],
        "programs": s["number_of_programs"], "learning": s["learning_time_seconds"],
        "core": s["popper_time_seconds"], "client_eval": ev,
        "overhead": max(s["federation_time_seconds"] - ev, 0.0),
    }


def log(c, exp):
    return [(r["hypothesis"], r["epsilon_positive"], r["epsilon_negative"]) for r in c.execute(
        "select hypothesis, epsilon_positive, epsilon_negative from hypothesis_log "
        "where experiment_id=? and not is_final_validation order by sequence_number", (exp,))]


def ms(values, d=2):
    if not values:
        return "-"
    m = st.mean(values)
    return f"{m:.{d}f} ± {st.pstdev(values):.{d}f}" if len(values) > 1 else f"{m:.{d}f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "data" / "filp_platform.db"))
    ap.add_argument("--approach", choices=["coordination", "collaboration"])
    ap.add_argument("--benchmarks", type=int, nargs="*", default=[])
    a = ap.parse_args()
    c = connect(a.db)
    approaches = [a.approach] if a.approach else ["coordination", "collaboration"]

    perf, equiv = [], []
    for f, t in pairs(c, approaches, set(a.benchmarks)):
        fr, tr = run_ids(c, f["id"]), run_ids(c, t["id"])
        setting = (f["approach"], f["dataset"], f["number_of_clients"], f["partition_strategy"], f["base_seed"])
        fm, tm = [], []
        for n in sorted(set(fr) & set(tr)):
            mf, mt = metrics(c, fr[n]), metrics(c, tr[n])
            if mf is None or mt is None:
                continue
            fm.append(mf); tm.append(mt)
            lf, lt = log(c, fr[n]), log(c, tr[n])
            first = next((i for i, (x, y) in enumerate(zip(lf, lt), 1) if x != y), None)
            if first is None and len(lf) != len(lt):
                first = min(len(lf), len(lt)) + 1
            equiv.append({
                "approach": f["approach"], "dataset": f["dataset"], "K": f["number_of_clients"],
                "partition": f["partition_strategy"], "run": n, "benchmark": f["id"],
                "twin": t["id"], "programs_fed": len(lf), "programs_c0": len(lt),
                "identical": first is None, "first_difference": first or "",
                "solution_fed": mf["found"], "solution_c0": mt["found"]})
        for label, ms_ in (("federated", fm), ("client 0", tm)):
            if not ms_:
                continue
            perf.append({
                "approach": f["approach"], "dataset": f["dataset"], "K": f["number_of_clients"],
                "partition": f["partition_strategy"], "search": label, "runs": len(ms_),
                "solved": sum(m["found"] for m in ms_),
                "rounds": ms([m["rounds"] for m in ms_], 1),
                "programs": ms([m["programs"] for m in ms_], 1),
                "learning": ms([m["learning"] for m in ms_]), "core": ms([m["core"] for m in ms_]),
                "client_eval": ms([m["client_eval"] for m in ms_]),
                "overhead": ms([m["overhead"] for m in ms_])})

    OUT.mkdir(exist_ok=True)
    for name, rows in (("hybrid_performance", perf), ("hybrid_equivalence", equiv)):
        if not rows:
            print(f"(no data for {name})"); continue
        with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        print(f"\n== {name} ==")
        for r in rows:
            print("  ".join(str(v) for v in r.values()))
    print(f"\nCSV written to {OUT}")


if __name__ == "__main__":
    main()
