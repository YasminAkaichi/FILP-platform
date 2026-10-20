"""
Exact MDL combine from *signature tables* (no example identifiers).

Context
-------
Popper v3's COMBINE step picks the subset S of promising rules that
minimises

    cost(S) = size(S) + fn(S) + fp(S)

Whether an example is covered by S only depends on WHICH pool rules cover
it, i.e. on its *signature*: the set of pool-rule ids that cover it. Two
examples with the same signature are interchangeable for COMBINE. So each
client can reduce its local data to a table

    positives: {signature -> number of local positives with that signature}
    negatives: {signature -> number of local negatives with that signature}

and the server only needs the SUM of these tables over clients. Nothing in
them identifies an individual example, yet the optimisation is exactly the
same as the per-example one (each signature group is one weighted soft
constraint instead of `count` unit-weight ones).

This module is independent from popper_mdl.combine_mdl.Combiner (which is
built around per-example coverage sets); the vendored Popper-v3 is not
modified.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, List, Sequence, Tuple

import clingo

Signature = Tuple[int, ...]

_ENCODING = """
#show rule/1.
{ rule(R) } :- size(R,_).
:~ rule(R), size(R,K). [K@1, R]
covered(S) :- sig_rule(S,R), rule(R).
:~ pos_sig(S,W), not covered(S). [W@1, S, p]
:~ neg_sig(S,W), covered(S). [W@1, S, n]
"""


def merge_tables(tables: Iterable[Iterable[Tuple[Sequence[int], int]]]) -> Dict[Signature, int]:
    """Sum several clients' tables (same signature -> counts added)."""
    merged: Counter = Counter()
    for table in tables:
        for signature, count in table:
            merged[tuple(sorted(int(r) for r in signature))] += int(count)
    return dict(merged)


def combine_from_coverage(
    rule_sizes: Dict[int, int],
    pos_covered: Dict[int, "frozenset[int]"],
    neg_covered: Dict[int, "frozenset[int]"],
    num_pos: int,
) -> Tuple[List[int], int, int, int]:
    """
    Exact MDL combine from per-example coverage, i.e. the MaxSAT encoding of
    the MaxSynth paper:
        c_e -> OR p_h        (positive e, h covering e)
        c_e <- p_h           (negative e, h covering e)
        soft (not p_h) with weight size(h); soft (c_e) / (not c_e), weight 1.

    pos_covered / neg_covered : {rule_id: set of GLOBAL example positions
    covered by that rule}. num_pos is the global number of positives (the
    positives no pool rule covers are a constant cost).

    Examples with the same set of covering rules give identical clauses, so
    they are merged into one weighted constraint before calling the solver
    (same optimum, smaller problem).
    """
    pos_sig: Dict[int, List[int]] = {}
    for rule_id, covered in pos_covered.items():
        for e in covered:
            pos_sig.setdefault(e, []).append(rule_id)
    neg_sig: Dict[int, List[int]] = {}
    for rule_id, covered in neg_covered.items():
        for e in covered:
            neg_sig.setdefault(e, []).append(rule_id)

    pos_table: Counter = Counter(tuple(sorted(v)) for v in pos_sig.values())
    pos_table[()] += num_pos - len(pos_sig)          # positives nobody covers
    neg_table: Counter = Counter(tuple(sorted(v)) for v in neg_sig.values())
    return combine_signatures(rule_sizes, dict(pos_table), dict(neg_table))


def combine_signatures(
    rule_sizes: Dict[int, int],
    pos_table: Dict[Signature, int],
    neg_table: Dict[Signature, int],
) -> Tuple[List[int], int, int, int]:
    """
    rule_sizes : {rule_id: size in literals} for every rule of the pool.
    pos_table  : {signature: number of positives with that signature},
                 summed over all clients. The empty signature () counts the
                 positives no pool rule covers (a constant cost).
    neg_table  : same for negatives.

    Returns (selected_rule_ids, cost, tp, fp) where cost = size + fn + fp
    over the whole (federated) data, exactly as the centralised combine.
    """
    lines: List[str] = []
    for rule_id, size in rule_sizes.items():
        lines.append(f"size({rule_id},{int(size)}).")

    signature_id = {}

    def sid(signature: Signature) -> int:
        if signature not in signature_id:
            signature_id[signature] = len(signature_id) + 1
            for rule_id in signature:
                lines.append(f"sig_rule({signature_id[signature]},{rule_id}).")
        return signature_id[signature]

    for signature, count in pos_table.items():
        if count > 0:
            lines.append(f"pos_sig({sid(signature)},{int(count)}).")
    for signature, count in neg_table.items():
        # A negative whose signature is empty can never be covered.
        if count > 0 and signature:
            lines.append(f"neg_sig({sid(signature)},{int(count)}).")

    control = clingo.Control(["--warn=none"])
    control.add("base", [], _ENCODING + "\n".join(lines))
    control.ground([("base", [])])

    selected: List[int] = []
    cost = None
    with control.solve(yield_=True) as handle:
        for model in handle:  # the last model is the optimum
            cost = model.cost[0] if model.cost else 0
            selected = [
                atom.arguments[0].number
                for atom in model.symbols(shown=True)
                if atom.name == "rule"
            ]

    chosen = set(selected)
    tp = sum(c for sig, c in pos_table.items() if chosen.intersection(sig))
    fp = sum(c for sig, c in neg_table.items() if chosen.intersection(sig))
    size = sum(rule_sizes[r] for r in chosen)
    num_pos = sum(pos_table.values())
    # cost recomputed from the selection: robust to a model-less run
    cost = size + (num_pos - tp) + fp
    return sorted(selected), cost, tp, fp
