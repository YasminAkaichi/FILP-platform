"""Does the per-example evaluation time limit explain the differences between runs?

Some programs of the Trains1000 runs get a different score from one run to
another (see the Comparison paragraph of the thesis). The platform evaluates each
example with a wall-clock limit (FILP_EVAL_TIMEOUT, 0.1 s for the federated
approaches): an example that is not proved within the limit counts as "not
covered". On a busy machine this can change the score of a program.

This script checks it. It takes the programs whose answer differs between the
runs of a federated benchmark and of its client 0 benchmark, evaluates each of
them on the whole dataset several times, in parallel (to put the machine under
a load like the one of a federated run), with several time limits, and prints
the scores obtained.

    python scripts/check_eval_timeout.py --fed 300 --c0 301 --dataset trains1000

Reading the result: if the scores of a program vary with the limit 0.1 s and are
constant (and larger or equal) with a long limit, the time limit explains the
differences. If they still vary with a long limit, something else does.
"""

from __future__ import annotations

import argparse
import collections
import sqlite3
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "symbolic" / "popper-core"))
DB = ROOT / "data" / "filp_platform.db"


def _runs(connection, benchmark_id):
    return [
        dict(r)
        for r in connection.execute(
            "SELECT run_number, experiment_id FROM benchmark_runs "
            "WHERE benchmark_id = ? ORDER BY run_number",
            (benchmark_id,),
        )
    ]


def _log(connection, experiment_id):
    return [
        dict(r)
        for r in connection.execute(
            "SELECT sequence_number, hypothesis, score, epsilon_positive AS ep, "
            "epsilon_negative AS en FROM hypothesis_log "
            "WHERE experiment_id = ? AND is_final_validation = 0 ORDER BY sequence_number",
            (experiment_id,),
        )
    ]


def programs_with_different_answers(fed_benchmark: int, c0_benchmark: int) -> list[dict]:
    """Programs that obtain several scores or outcomes over the runs of the two
    benchmarks."""
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    seen: dict = collections.defaultdict(lambda: {"text": None, "answers": set()})
    for benchmark in (fed_benchmark, c0_benchmark):
        for run in _runs(connection, benchmark):
            for entry in _log(connection, run["experiment_id"]):
                key = tuple(sorted(l.strip() for l in entry["hypothesis"].splitlines() if l.strip()))
                item = seen[key]
                item["text"] = item["text"] or entry["hypothesis"]
                item["answers"].add((float(entry["score"]), entry["ep"], entry["en"]))
    return [
        {"text": v["text"], "answers": sorted(v["answers"])}
        for v in seen.values()
        if len(v["answers"]) > 1
    ]


_TESTERS: dict = {}


def try_orders(job):
    """Evaluate a program with several orders of its body literals and print the
    score and the time of each, with the platform's limit and with a long one.
    The order of the literals changes the time a program needs, hence which
    examples are counted as not covered when the limit is short."""
    import random
    import re
    import time

    dataset, text, count, seed, long_limit = job
    head, body = text.strip().rstrip(".").split(":-", 1)
    literals = re.findall(r"\w+\([^()]*\)", body)
    rng = random.Random(seed)
    orders = [list(literals)]
    for _ in range(count - 1):
        shuffled = list(literals)
        rng.shuffle(shuffled)
        orders.append(shuffled)
    print(f"  score@0.1s  time@0.1s | score@{long_limit:g}s  time@{long_limit:g}s | order of the body literals",
          flush=True)
    for order in orders:
        program = f"{head.strip()} :- {','.join(order)}."
        measured = []
        for limit in (0.1, long_limit):
            start = time.perf_counter()
            score = evaluate((dataset, program, limit, 1))[0][0]
            measured.append((score, time.perf_counter() - start))
        (s1, t1), (s2, t2) = measured
        # One line per order, printed as soon as it is known (a bad order can be slow).
        print(f"  {s1:>9.0f}  {t1:>8.2f}s | {s2:>8.0f}  {t2:>7.2f}s | {','.join(order)}", flush=True)
    return []


def _run_alone_job(function, job):
    with Pool(1, maxtasksperchild=1) as pool:
        return pool.apply(function, (job,))


def _run_alone(job):
    """Evaluate in a fresh process: pyswip has a single Prolog engine per process,
    so two datasets cannot be loaded in the same process."""
    with Pool(1, maxtasksperchild=1) as pool:
        return pool.apply(evaluate, (job,))


def compare_with_partitions(programs, dataset: str, partitions: str, timeout: float) -> None:
    """Score of each program on the whole dataset, and sum of its scores on the
    partitions of the clients. With a long limit nothing can time out, so a
    difference comes from the partition itself (or from the program)."""
    directory = ROOT / "datasets" / partitions
    parts = sorted(directory.glob(f"{dataset}_part*"), key=lambda p: int(p.name.rsplit("part", 1)[1]))
    print(f"Partitions: {[p.name for p in parts]}; time limit {timeout} s\n")
    for number, program in enumerate(programs, start=1):
        whole = _run_alone((dataset, program["text"], timeout, 1))[0]
        per_client = [
            _run_alone((str(p.relative_to(ROOT / "datasets")), program["text"], timeout, 1))[0]
            for p in parts
        ]
        total_score = sum(r[0] for r in per_client)
        total_tp = sum(r[1] for r in per_client)
        total_fp = sum(r[2] for r in per_client)
        print(f"Program {number}: {program['text'].strip()}")
        print(f"  scores in the logs: {sorted({a[0] for a in program['answers']})}")
        print(f"  whole dataset: score {whole[0]} (tp {whole[1]}, fp {whole[2]})")
        print(f"  clients: scores {[r[0] for r in per_client]}, sum {total_score} (tp {total_tp}, fp {total_fp})")
        print(f"  {'SAME' if (total_score, total_tp, total_fp) == whole else 'DIFFERENT'}\n")


def _tester(dataset: str):
    """One tester per process and dataset. pyswip has a single Prolog engine per
    process, so a second Tester in the same process would load the examples a
    second time and stack a second time limit: build it once and only change the
    time limit between evaluations."""
    if dataset not in _TESTERS:
        from popper.util import Settings
        from popper.tester import Tester

        directory = ROOT / "datasets" / dataset
        settings = Settings(
            bias_file=str(directory / "bias.pl"),
            ex_file=str(directory / "exs.pl"),
            bk_file=str(directory / "bk.pl"),
            timeout=60,
            eval_timeout=0.1,
        )
        _TESTERS[dataset] = Tester(settings)
    return _TESTERS[dataset]


def evaluate(job):
    """Evaluate one program on the whole dataset `repeats` times with the given
    limit. Returns a list of (score, tp, fp) tuples."""
    dataset, text, timeout, repeats = job
    tester = _tester(dataset)
    tester.prolog.retractall("timeout(_)")
    tester.prolog.assertz(f"timeout({timeout})")
    clauses = [l.strip().rstrip(".") for l in text.splitlines() if l.strip()]
    heads = {(c.split(":-")[0].split("(")[0], c.split(":-")[0].count(",") + 1) for c in clauses}
    results = []
    for _ in range(repeats):
        for clause in clauses:
            tester.prolog.assertz(clause)
        try:
            covered = set(next(tester.prolog.query("success_set(Xs)"))["Xs"])
        finally:
            for name, arity in heads:
                tester.prolog.retractall(f"{name}({','.join(['_'] * arity)})")
        positives, negatives = set(tester.pos), set(tester.neg)
        tp = len(covered & positives)
        fp = len(covered & negatives)
        tn = len(negatives) - fp
        results.append((tp + tn, tp, fp))
    return results


def evaluate_sets(job):
    """Like evaluate, but returns, for each repetition, the set of the examples
    that the program covers (positive ids > 0, negative ids < 0)."""
    dataset, text, timeout, repeats = job
    tester = _tester(dataset)
    tester.prolog.retractall("timeout(_)")
    tester.prolog.assertz(f"timeout({timeout})")
    clauses = [l.strip().rstrip(".") for l in text.splitlines() if l.strip()]
    heads = {(c.split(":-")[0].split("(")[0], c.split(":-")[0].count(",") + 1) for c in clauses}
    sets = []
    for _ in range(repeats):
        for clause in clauses:
            tester.prolog.assertz(clause)
        try:
            sets.append(frozenset(next(tester.prolog.query("success_set(Xs)"))["Xs"]))
        finally:
            for name, arity in heads:
                tester.prolog.retractall(f"{name}({','.join(['_'] * arity)})")
    return sets


def example_times(job):
    """Time of the evaluation of each example, by id (no time limit)."""
    dataset, text = job
    tester = _tester(dataset)
    tester.prolog.retractall("timeout(_)")
    tester.prolog.assertz("timeout(60)")
    clauses = [l.strip().rstrip(".") for l in text.splitlines() if l.strip()]
    heads = {(c.split(":-")[0].split("(")[0], c.split(":-")[0].count(",") + 1) for c in clauses}
    tester.prolog.retractall("time_ex(_,_)")
    tester.prolog.assertz(
        "(time_ex(ID,T) :- ex_index(ID,A), get_time(W0), "
        "(catch(call_with_time_limit(60,call(A)),_,fail) -> true ; true), "
        "get_time(W1), T is W1-W0)"
    )
    for clause in clauses:
        tester.prolog.assertz(clause)
    try:
        pairs = next(tester.prolog.query("findall([ID,T], time_ex(ID,T), L)"))["L"]
    finally:
        for name, arity in heads:
            tester.prolog.retractall(f"{name}({','.join(['_'] * arity)})")
    return {int(i): float(t) for i, t in pairs}


def profile(job):
    """Time of the evaluation of each example (no time limit, in seconds): the
    examples that need more than the limit are the ones counted as not covered."""
    dataset, text = job
    tester = _tester(dataset)
    tester.prolog.retractall("timeout(_)")
    tester.prolog.assertz("timeout(60)")
    clauses = [l.strip().rstrip(".") for l in text.splitlines() if l.strip()]
    heads = {(c.split(":-")[0].split("(")[0], c.split(":-")[0].count(",") + 1) for c in clauses}
    tester.prolog.retractall("time_ex(_,_)")
    tester.prolog.assertz(
        "(time_ex(ID,T) :- ex_index(ID,A), get_time(W0), "
        "(catch(call_with_time_limit(60,call(A)),_,fail) -> true ; true), "
        "get_time(W1), T is W1-W0)"
    )
    for clause in clauses:
        tester.prolog.assertz(clause)
    try:
        times = list(next(tester.prolog.query("findall(T, time_ex(_,T), L)"))["L"])
    finally:
        for name, arity in heads:
            tester.prolog.retractall(f"{name}({','.join(['_'] * arity)})")
    return sorted(float(t) for t in times)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fed", type=int, required=True, help="benchmark id of the federated runs")
    parser.add_argument("--c0", type=int, required=True, help="benchmark id of the client 0 runs")
    parser.add_argument("--dataset", default="trains1000")
    parser.add_argument("--timeouts", type=float, nargs="+", default=[0.001, 0.01, 0.1, 1.0, 10.0])
    parser.add_argument("--repeats", type=int, default=3, help="evaluations per process")
    parser.add_argument("--load", type=int, default=4, help="processes evaluating at the same time")
    parser.add_argument("--profile", action="store_true",
                        help="print, for each program, how long its slowest examples take (one process)")
    parser.add_argument("--partitions", default=None,
                        help="directory of the client datasets under datasets/ "
                             "(e.g. generated/trains1000/iid_3_seed_42): compare the whole dataset "
                             "with the sum over the clients, with a long time limit")
    parser.add_argument("--long-limit", type=float, default=1.0,
                        help="long time limit of the --orders mode, in seconds (a slow order with a "
                             "long limit can take a very long time)")
    parser.add_argument("--orders", type=int, default=0,
                        help="evaluate each program with this many orders of its body literals "
                             "(0.1 s and 10 s limits) and print the score and time of each")
    parser.add_argument("--flaky", action="store_true",
                        help="find the examples whose coverage changes from one evaluation to another "
                             "(time limit of 0.1 s, several processes at the same time) and print their time")
    args = parser.parse_args()

    programs = programs_with_different_answers(args.fed, args.c0)
    print(f"{len(programs)} program(s) with different answers in the logs of #{args.fed} and #{args.c0}.\n")

    if args.orders:
        for number, program in enumerate(programs, start=1):
            print(f"Program {number}: {program['text'].strip()}")
            print(f"  scores in the logs: {sorted({a[0] for a in program['answers']})}")
            _run_alone_job(try_orders, (args.dataset, program["text"], args.orders, 1, args.long_limit))
            print()
        return

    if args.partitions:
        compare_with_partitions(programs, args.dataset, args.partitions, timeout=10.0)
        return

    if args.flaky:
        with Pool(args.load) as pool:
            for number, program in enumerate(programs, start=1):
                jobs = [(args.dataset, program["text"], 0.1, args.repeats)] * args.load
                sets = [s for chunk in pool.map(evaluate_sets, jobs) for s in chunk]
                union = frozenset().union(*sets)
                common = frozenset.intersection(*sets)
                flaky = sorted(union - common)
                times = example_times((args.dataset, program["text"]))
                print(f"Program {number}: {program['text'].strip()}")
                print(f"  {len(sets)} evaluations; examples covered in some evaluations and not in others: {len(flaky)}")
                for ident in flaky:
                    covered = sum(1 for s in sets if ident in s)
                    kind = "positive" if ident > 0 else "negative"
                    print(f"    example {ident} ({kind}): covered in {covered}/{len(sets)} evaluations, "
                          f"takes {times.get(ident, float('nan')):.3f} s alone")
                print()
        return

    if args.profile:
        for number, program in enumerate(programs, start=1):
            times = profile((args.dataset, program["text"]))
            over = lambda limit: sum(1 for t in times if t > limit)
            print(f"Program {number}: {program['text'].strip()}")
            print(f"  scores in the logs: {sorted({a[0] for a in program['answers']})}")
            print(f"  {len(times)} examples; slowest {times[-1]:.3f} s, median {times[len(times) // 2]:.4f} s")
            print(f"  examples slower than 0.001 s: {over(0.001)}, 0.01 s: {over(0.01)}, "
                  f"0.1 s: {over(0.1)}, 1 s: {over(1.0)}\n")
        return

    with Pool(args.load) as pool:
        for number, program in enumerate(programs, start=1):
            print(f"Program {number}: {program['text'].strip()}")
            print(f"  scores in the logs: {sorted({a[0] for a in program['answers']})}")
            for timeout in args.timeouts:
                jobs = [(args.dataset, program["text"], timeout, args.repeats)] * args.load
                scores = [r[0] for chunk in pool.map(evaluate, jobs) for r in chunk]
                counts = collections.Counter(scores)
                spread = f"{min(scores):.0f}..{max(scores):.0f}" if len(counts) > 1 else f"{scores[0]:.0f}"
                print(f"  time limit {timeout:>5} s: {len(scores)} evaluations, scores {spread}"
                      f"  ({'varies' if len(counts) > 1 else 'constant'})")
            print()


if __name__ == "__main__":
    main()
