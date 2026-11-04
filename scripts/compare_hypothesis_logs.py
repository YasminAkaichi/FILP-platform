"""Compare, round by round, two searches of the hybrid evaluation.

Usage (from the project root):

    python scripts/compare_hypothesis_logs.py <federated benchmark id> [run number]

For the federated Coordination benchmark <id>, finds its "Client 0
(centralized)" twin ("Centralized testing, whole <dataset> · same seed as
#<id>") and compares the hypotheses tested by both searches, run by run:
the first round where the two searches test a different program, and, if
the same program was tested, whether the outcome / score / rule feedback
agree. Needs runs launched after hypothesis_log was added to Coordination.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "filp_platform.db"


def _runs(connection, benchmark_id):
    return {
        int(r["run_number"]): int(r["experiment_id"])
        for r in connection.execute(
            "SELECT run_number, experiment_id FROM benchmark_runs WHERE benchmark_id = ?",
            (benchmark_id,),
        )
    }


def _log(connection, experiment_id):
    rows = connection.execute(
        "SELECT sequence_number, hypothesis, score, epsilon_positive, epsilon_negative "
        "FROM hypothesis_log WHERE experiment_id = ? AND is_final_validation = 0 "
        "ORDER BY sequence_number",
        (experiment_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def _flags(experiment_id):
    path = ROOT / "artifacts" / f"experiment_{experiment_id}" / "hypothesis_log.json"
    if not path.is_file():
        return {}
    return {e["sequence_number"]: e for e in json.loads(path.read_text(encoding="utf-8"))}


def _norm(text: str) -> str:
    return "\n".join(sorted(line.strip() for line in text.splitlines() if line.strip()))


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    federated_id = int(sys.argv[1])
    only_run = int(sys.argv[2]) if len(sys.argv) > 2 else None

    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row

    twin = connection.execute(
        "SELECT id FROM benchmarks WHERE name LIKE ? ORDER BY id DESC LIMIT 1",
        (f"Centralized testing, whole % same seed as #{federated_id}",),
    ).fetchone()
    if twin is None:
        raise SystemExit(f"No 'Client 0 (centralized)' benchmark linked to #{federated_id}.")

    fed_runs, cen_runs = _runs(connection, federated_id), _runs(connection, int(twin["id"]))

    for run in sorted(fed_runs):
        if only_run is not None and run != only_run:
            continue
        if run not in cen_runs:
            continue
        fed, cen = _log(connection, fed_runs[run]), _log(connection, cen_runs[run])
        print(f"\n===== Run {run}: federated #{fed_runs[run]} ({len(fed)} programs) "
              f"vs client 0 #{cen_runs[run]} ({len(cen)} programs) =====")
        if not fed or not cen:
            print("  No hypothesis log (run launched before the log existed).")
            continue

        same_program_diff_answer = 0
        for index, (a, b) in enumerate(zip(fed, cen), start=1):
            if _norm(a["hypothesis"]) != _norm(b["hypothesis"]):
                print(f"  First different program at round {index}.")
                print(f"    federated : {a['hypothesis']!r}  outcome=({a['epsilon_positive']},{a['epsilon_negative']}) score={a['score']}")
                print(f"    client 0  : {b['hypothesis']!r}  outcome=({b['epsilon_positive']},{b['epsilon_negative']}) score={b['score']}")
                prev = fed[index - 2] if index > 1 else None
                if prev:
                    pf = _flags(fed_runs[run]).get(prev["sequence_number"], {})
                    pc = _flags(cen_runs[run]).get(prev["sequence_number"], {})
                    print(f"    previous program (same in both): outcome fed=({prev['epsilon_positive']},{prev['epsilon_negative']}) "
                          f"client0=({cen[index-2]['epsilon_positive']},{cen[index-2]['epsilon_negative']}); "
                          f"score fed={prev['score']} client0={cen[index-2]['score']}")
                    print(f"    previous rule feedback: inconsistent fed={pf.get('inconsistent_rules')} client0={pc.get('inconsistent_rules')}; "
                          f"totally incomplete fed={pf.get('totally_incomplete_rules')} client0={pc.get('totally_incomplete_rules')}")
                break
            if (a["epsilon_positive"], a["epsilon_negative"]) != (b["epsilon_positive"], b["epsilon_negative"]) or abs(a["score"] - b["score"]) > 1e-9:
                same_program_diff_answer += 1
        else:
            print(f"  The first {min(len(fed), len(cen))} programs are identical.")
        print(f"  Same program but different outcome/score before the first split: {same_program_diff_answer}")


if __name__ == "__main__":
    main()
