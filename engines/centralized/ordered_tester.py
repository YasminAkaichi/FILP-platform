"""Tester used by the centralized Popper run.

Same evaluation as the federated clients (engines/collaboration/client.py,
class OrderedTester): each clause is asserted in Prolog with its literals in the
order given by Popper's generator.

Popper's own Tester.using() reorders the body through a Python set
(Clause.to_ordered). With PYTHONHASHSEED fixed by the launcher, that order is
the same in every run, but for some programs it is a bad join order: almost
every example then hits the per-example time limit (FILP_EVAL_TIMEOUT, 0.1 s),
and one test of Trains1000 takes ~98 s instead of a few ms. Using the order of
the generator gives the centralized run the same evaluation as the clients, so
the two are comparable.
"""

from __future__ import annotations

from contextlib import contextmanager

from popper.core import Clause
from popper.tester import Tester


class OrderedTester(Tester):
    @contextmanager
    def using(self, rules):
        current_clauses = set()
        try:
            for rule in rules:
                head, _ = rule
                self.prolog.assertz(Clause.to_code(rule))
                current_clauses.add((head.predicate, head.arity))
            yield
        finally:
            for predicate, arity in current_clauses:
                args = ','.join(['_'] * arity)
                self.prolog.retractall(f'{predicate}({args})')
