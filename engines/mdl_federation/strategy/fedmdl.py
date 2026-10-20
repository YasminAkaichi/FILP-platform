"""
FedMDL — federated version of MaxSynth / noisy-MDL (symbolic/Popper-v3),
mirroring the shape of engines/collaboration/strategy/fedpopper.py (FedPopper,
the federated version of Popper 1.1.0) as closely as the two engines'
internals allow.

Same bridge pattern as FedPopper: a background thread (`_fedmdl_loop`) owns
the ASP-based candidate generation (via popper_mdl's own `Generator`), and
talks to Flower's `configure_fit`/`aggregate_fit` (running on Flower's own
thread) through two `threading.Event`s. See EarlyStopSignal below for why
Flower's round loop is stopped via a raised exception rather than returning
`[]` from configure_fit.

Where this genuinely differs from FedPopper, because MaxSynth's own
centralized algorithm differs from Popper 1.1.0's:

  - Candidate generation does not (yet) use a per-round ASP constraint
    feedback loop. Popper's generalisation/specialisation/banish
    constraints prune the *search space* as soon as a rule is found
    inconsistent/incomplete; MaxSynth's noisy mode instead keeps
    imperfect rules that are "promising" (loop.py: tp >= size + fp,
    tp >= size, fp + size < best_mdl) and prunes with its own bounds. This
    version applies the promising test and the size bound
    max_literals = best_mdl - 1, but does not re-implement Popper-v3's
    other pruning (specialisation/generalisation constraints, MUCs,
    seen_hyp_spec/seen_hyp_gen, bkcons, datalog mode, recursion, predicate
    invention) — it drives the plain non-recursive, non-PI, single-rule
    generate loop, same shape as `parse_model_single_rule` in
    popper_mdl/loop.py's default path.

  - There is no "exact solution found" stop condition. `early_stop` here
    only fires on timeout or once the generator's search space (bounded by
    max_literals / (max_body, max_rules) and by best_mdl - 1) is
    exhausted — MDL's optimum is whatever the combine step picks from the
    accumulated "promising program" pool, not a single rule matching
    ("all", "none").

  - Per-round client feedback is NOT a 3-valued all/some/none outcome. Each
    client tests the received candidate locally (popper_mdl.tester.Tester.
    test_single_rule_pos / ..._neg) and answers, for ITS examples, "is this
    example covered by the rule?" as the list of covered local positions.
    The server only knows how many examples each client has (registration
    round) and therefore who owns which global position; it never sees the
    examples. This gives it, for every pool rule h and example e, whether
    B u h |= e: exactly what the MaxSAT encoding of the MaxSynth paper
    needs (c_e -> OR p_h ...), so COMBINE runs on the server, in batches
    during the search like popper_mdl/loop.py, and every improvement lowers
    best_mdl and the size bound (max_literals = best_mdl - 1).

  - combine_mode="signatures" is a privacy variant: the clients send only
    two counts per candidate, and one last round returns a table
    {signature -> number of local positives / negatives} (the signature of
    an example is the set of pool rules covering it); one weighted combine
    (engines/mdl_federation/signature_combiner.py) runs at the end. Same
    optimum, no per-example coverage pattern leaves the clients.

  - Registration round (round 1): every client sends its local
    (num_pos, num_neg); the server builds the global inventory
    (`_register_client_counts`).
"""

from __future__ import annotations

import json
import threading
import time
from logging import INFO, WARNING

from flwr.common import FitIns, EvaluateIns, ndarrays_to_parameters, parameters_to_ndarrays
from flwr.common.logger import log
from flwr.server.strategy import Strategy
from flwr.server.strategy.aggregate import weighted_loss_avg

import numpy as np

from popper_mdl.generate import Generator, Grounder, parse_model_single_rule
from popper_mdl.util import Stats, calc_prog_size, reduce_prog

from engines.mdl_federation.rule_codec import rule_to_text
from engines.mdl_federation.signature_combiner import (
    combine_from_coverage,
    combine_signatures,
    merge_tables,
)

WARNING_MIN_AVAILABLE_CLIENTS_TOO_LOW = """
Setting `min_available_clients` lower than `min_fit_clients` can cause the
server to fail when there are too few clients connected to the server.
"""


class EarlyStopSignal(Exception):
    """Raised from configure_fit() once the FedMDL loop has finished
    (timeout or search space exhausted) to break out of Flower's
    Server.fit() round loop immediately, exactly like FedPopper's
    EarlyStopSignal — see that class's docstring in
    engines/collaboration/strategy/fedpopper.py for the full rationale
    (returning [] only skips one round and lets Flower coast through
    every remaining configured round, num_rounds defaults to 35000+).
    engines/mdl_federation/server.py catches this specific exception
    type and treats it as a normal, successful termination.
    """



class FedMDL(Strategy):
    def __repr__(self):
        return "FedMDL"

    def __init__(
        self,
        settings,
        stats=None,
        fraction_fit: float = 1.0,
        fraction_evaluate: float = 0.0,
        min_fit_clients: int = 2,
        min_evaluate_clients: int = 0,
        min_available_clients: int = 2,
        accept_failures: bool = False,
        with_suspension: bool = True,
        timeout_seconds: float = 600.0,
        combine_mode: str = "indices",
    ):
        super().__init__()

        if combine_mode not in ("indices", "signatures"):
            raise ValueError(f"combine_mode must be 'indices' or 'signatures', got {combine_mode!r}")
        self.combine_mode = combine_mode

        if min_fit_clients > min_available_clients:
            log(WARNING, WARNING_MIN_AVAILABLE_CLIENTS_TOO_LOW)

        self.settings = settings
        self.stats = stats if stats is not None else Stats(info=settings.info)

        self.fraction_fit = fraction_fit
        self.fraction_evaluate = fraction_evaluate
        self.min_fit_clients = min_fit_clients
        self.min_evaluate_clients = min_evaluate_clients
        self.min_available_clients = min_available_clients
        self.accept_failures = accept_failures
        self.timeout_seconds = timeout_seconds

        # Final result, populated only once by `_finalize()` at the very
        # end of `_fedmdl_loop` (timeout or search exhausted).
        self.solution_program = None       # (head, body) tuple, or None
        self.solution_score = None         # (tp, fn, tn, fp, size), or None
        self.solution_found = False        # True iff combine returned a program
        self.early_stop = False

        self.pool_size = 0                 # how many "promising" candidates were kept
        self.total_candidates_tested = 0

        self.hypothesis_log: list[dict] = []

        self.startup_time = None
        self.learning_start = None
        self.learning_time = None

        self._hyp_ready = threading.Event()
        self._fb_ready = threading.Event()
        self._lock = threading.Lock()
        self._current_rule_text = None
        self._current_cand_id = None
        self._current_fb = None            # (tp, fp, pos_set|None, neg_set|None)

        # Best bound seen so far (single rules and combinations) and best
        # combination found: (pool ids, cost, tp, fp).
        self.best_mdl: int | None = None
        self.best_solution_cost: int | None = None
        self.best_solution = None
        self._size_cap = 0
        self._pending_new = 0

        # Final "signatures" round (combine_mode == "signatures" only).
        self._search_done = False          # the generate loop has ended
        self._sig_round_sent = False       # configure_fit issued the sig round
        self._sig_pool_ids: list[int] = []
        self._sig_tables = None            # (pos_table, neg_table) or None
        self._sig_ready = threading.Event()

        self.with_suspension = with_suspension
        self.timer = time.perf_counter if self.with_suspension else time.process_time

        self.t_core = 0.0          # time spent in local ASP generate work
        self.t_federation = 0.0    # time spent waiting on the federation round-trip
        self.global_start = self.timer()
        self.last_round = 0

        # Global index bookkeeping — set once, the first time every
        # expected client has reported its local (num_pos, num_neg) counts
        # (see `_register_client_counts`). Until then, `num_pos_global`/
        # `num_neg_global` are None and the loop blocks waiting for them.
        self._client_pos_offset: dict[str, int] = {}
        self._client_neg_offset: dict[str, int] = {}
        self.num_pos_global: int | None = None
        self.num_neg_global: int | None = None
        self._registration_ready = threading.Event()

        self._fedmdl_thread = threading.Thread(
            target=self._fedmdl_loop,
            daemon=True,
            name="FedMDLLoop",
        )
        self._fedmdl_thread.start()

    # ------------------------------------------------------------------
    # Global index bookkeeping
    # ------------------------------------------------------------------

    def _register_client_counts(self, counts_by_client: dict[str, tuple[int, int]]) -> None:
        """
        counts_by_client: {client_id_str: (num_pos_local, num_neg_local)}
        Called once, the first time `aggregate_fit` sees a fully successful
        round (all expected clients responded) — assigns each client a
        fixed, deterministic offset into one global positive index range
        and one global negative index range, ordered by client_id so every
        client computes the same ordering independently if ever needed.
        """
        if self.num_pos_global is not None:
            return  # already registered

        pos_offset = 0
        neg_offset = 0
        for client_id in sorted(counts_by_client.keys()):
            num_pos_local, num_neg_local = counts_by_client[client_id]
            self._client_pos_offset[client_id] = pos_offset
            self._client_neg_offset[client_id] = neg_offset
            pos_offset += num_pos_local
            neg_offset += num_neg_local

        self.num_pos_global = pos_offset
        self.num_neg_global = neg_offset
        self.settings.pos_index = list(range(self.num_pos_global))
        self.settings.neg_index = list(range(self.num_neg_global))

        log(
            INFO,
            f"[FedMDL] Registered {len(counts_by_client)} client(s): "
            f"{self.num_pos_global} positive / {self.num_neg_global} "
            "negative examples globally.",
        )

        self._registration_ready.set()

    # ------------------------------------------------------------------
    # FEDMDL LOOP — runs in its own thread. Generates candidates via
    # popper_mdl's own ASP Generator (bias-only, no example data needed —
    # see Settings.__init__ in popper_mdl/util.py) and dispatches each one
    # to the clients via `_send_and_wait`.
    #
    # The server keeps an inventory of the examples (client c owns the
    # global positions [offset_c, offset_c + n_c)) but never sees their
    # content. For each candidate rule the clients answer, for THEIR
    # examples, "is this example covered by the rule?". From the global
    # coverage the server computes the MDL cost of the single rule and
    # applies Popper v3's own "promising rule" test (loop.py):
    #     tp >= size + fp, tp >= size, fp + size < best_mdl.
    # Promising rules go to the pool.
    #
    # combine_mode == "indices" (default, the encoding of the MaxSynth
    #   paper): the server then holds, for every pool rule h and every
    #   example e, whether B u h |= e, so it can build the MaxSAT encoding
    #   (c_e -> OR p_h ...) and COMBINE while the search is running, in
    #   batches exactly like popper_mdl/loop.py (batch_size, size change).
    #   Every improvement lowers best_mdl and with it the size bound
    #   (max_literals = best_mdl - 1), which prunes the search.
    #
    # combine_mode == "signatures" (privacy variant): the clients only send
    #   two counts per candidate; ONE last round asks them for their
    #   signature tables over the pool and ONE combine runs at the end.
    # ------------------------------------------------------------------

    def _fedmdl_loop(self) -> None:
        wall_start = self.timer()

        # Block until round 1 has told us the global example counts —
        # `configure_fit`/`aggregate_fit` unblock this the first time all
        # expected clients have reported in (see `_register_client_counts`).
        self._registration_ready.wait()

        grounder = Grounder(self.settings)
        generator = Generator(self.settings, grounder)

        # Search-space bound. popper_mdl's own noisy-mode loop additionally
        # caps this at num_pos (see popper_mdl/loop.py:popper()) — not
        # applied here, since that cap can exclude the true optimum on
        # datasets with very few positive examples relative to rule
        # complexity (observed directly on the "trains" dataset with the
        # centralized engine — see engines/centralized/mdl_runner.py's
        # usage notes). Bounded by max_body/max_rules/max_literals, then
        # lowered to best_mdl - 1 each time a better program is found.
        max_size = min(
            (1 + self.settings.max_body) * self.settings.max_rules,
            self.settings.max_literals,
        )
        self._size_cap = max_size

        num_pos = self.num_pos_global
        # pool: list of dicts {id, rule, size, pos, neg}; pos/neg are the
        # GLOBAL covered example positions (frozensets) in "indices" mode,
        # None in "signatures" mode.
        pool: list[dict] = []
        self._pending_new = 0     # pool entries added since the last combine
        # Same initial bound as popper_mdl/loop.py: the empty program.
        self.best_mdl = num_pos
        self.best_solution_cost = num_pos
        batch_size = int(getattr(self.settings, "batch_size", 20) or 20)

        try:
            for size in range(1, max_size + 1):
                if size > self._size_cap:
                    break

                # Size change: combine what is pending (as loop.py does).
                if self.combine_mode == "indices" and self._pending_new:
                    self._combine_pool(pool)
                    if size > self._size_cap:
                        break

                generator.update_solver(size, self.settings.max_vars, self.settings.max_rules)

                while True:
                    if self.timer() - wall_start > self.timeout_seconds:
                        raise StopIteration

                    if size > self._size_cap:
                        break  # a better program was found: this size is useless

                    generate_start = self.timer()
                    with self.stats.duration("generate"):
                        model = generator.get_model()
                    self.t_core += self.timer() - generate_start

                    if model is None:
                        break

                    atoms = model.symbols(shown=True)
                    prog, _before, _min_clause = parse_model_single_rule(self.settings, atoms)
                    self.stats.total_programs += 1
                    self.total_candidates_tested += 1
                    cand_id = self.total_candidates_tested
                    rule = list(prog)[0]
                    prog_size = calc_prog_size(frozenset([rule]))

                    tp, fp, pos_set, neg_set = self._send_and_wait(rule, cand_id)

                    # MDL of the single-rule program: fn + fp + size.
                    mdl = (num_pos - tp) + fp + prog_size
                    if mdl < self.best_mdl:
                        self.best_mdl = mdl
                        self._size_cap = min(self._size_cap, self.best_mdl - 1)

                    # Promising rule — same condition as the centralised
                    # Popper v3 loop (symbolic/Popper-v3/popper_mdl/loop.py).
                    if tp >= prog_size + fp and tp >= prog_size and fp + prog_size < self.best_mdl:
                        pool.append(
                            {
                                "id": cand_id,
                                "rule": rule,
                                "size": prog_size,
                                "pos": pos_set,
                                "neg": neg_set,
                            }
                        )
                        self._pending_new += 1
                        self.pool_size = len(pool)

                        self.hypothesis_log.append(
                            {
                                "sequence_number": len(self.hypothesis_log) + 1,
                                "hypothesis": rule_to_text(rule),
                                "positive_covered": tp,
                                "negative_covered": fp,
                                "size": size,
                            }
                        )

                        if self.combine_mode == "indices" and self._pending_new >= batch_size:
                            self._combine_pool(pool)
        except StopIteration:
            pass
        except Exception as error:  # noqa: BLE001 — never let the loop thread die silently
            log(WARNING, f"[FedMDL] Search loop stopped on error: {error}")
        finally:
            try:
                self._finalize(pool)
            except Exception as error:  # noqa: BLE001
                log(WARNING, f"[FedMDL] Finalisation failed: {error}")
            self.early_stop = True
            self._hyp_ready.set()

    # ------------------------------------------------------------------
    # COMBINE
    # ------------------------------------------------------------------

    def _record_solution(self, selected, cost, tp, fp) -> None:
        """Keep the best combination found so far (selected = pool ids)."""
        if selected and cost < self.best_solution_cost:
            self.best_solution_cost = cost
            self.best_solution = (list(selected), cost, tp, fp)
            if cost < self.best_mdl:
                self.best_mdl = cost
            self._size_cap = min(self._size_cap, self.best_mdl - 1)
            log(INFO, f"[FedMDL] New best combination: MDL cost {cost}, rules {list(selected)}")

    def _combine_pool(self, pool: list) -> None:
        """Exact MDL combine over the pool, from the per-example coverage
        the clients reported (the encoding of the MaxSynth paper)."""
        self._pending_new = 0
        if not pool:
            return
        rule_sizes = {e["id"]: e["size"] for e in pool}
        pos_cov = {e["id"]: e["pos"] for e in pool}
        neg_cov = {e["id"]: e["neg"] for e in pool}
        try:
            with self.stats.duration("combine"):
                selected, cost, tp, fp = combine_from_coverage(
                    rule_sizes, pos_cov, neg_cov, self.num_pos_global
                )
        except Exception as error:  # noqa: BLE001
            log(WARNING, f"[FedMDL] Combine step failed: {error}")
            return
        self._record_solution(selected, cost, tp, fp)

    def _finalize(self, pool: list) -> None:
        if not pool:
            log(INFO, "[FedMDL] No promising candidate was kept.")
            self.learning_time = self.timer() - (self.learning_start or self.timer())
            return

        if self.combine_mode == "indices":
            if self._pending_new:
                self._combine_pool(pool)
        else:
            # Signatures: ask the clients for their signature tables over
            # the pool — wake configure_fit (which turns this into the
            # "signatures" round) and wait for aggregate_fit to hand the
            # merged tables back.
            self._sig_pool_ids = [entry["id"] for entry in pool]
            self._search_done = True
            self._hyp_ready.set()
            self._sig_ready.wait(timeout=600)

            tables = self._sig_tables
            if tables is None:
                log(WARNING, "[FedMDL] No signature tables received: no combine possible.")
            else:
                pos_table, neg_table = tables
                rule_sizes = {entry["id"]: entry["size"] for entry in pool}
                try:
                    selected, cost, tp, fp = combine_signatures(rule_sizes, pos_table, neg_table)
                    self._record_solution(selected, cost, tp, fp)
                except Exception as error:  # noqa: BLE001
                    log(WARNING, f"[FedMDL] Combine step failed: {error}")

        if self.best_solution is not None:
            selected, cost, tp, fp = self.best_solution
            by_id = {entry["id"]: entry["rule"] for entry in pool}
            program = reduce_prog([by_id[i] for i in selected])
            size = calc_prog_size(program)
            fn = self.num_pos_global - tp
            tn = self.num_neg_global - fp
            self.solution_program = program
            self.solution_score = (tp, fn, tn, fp, size)
            self.solution_found = True
            log(
                INFO,
                f"[FedMDL] Combine finished: {len(program)} rule(s), "
                f"score={self.solution_score}, MDL cost={cost}",
            )
        else:
            log(INFO, "[FedMDL] Combine found no improving program.")

        self.learning_time = self.timer() - (self.learning_start or self.timer())

    def _send_and_wait(self, rule, cand_id):
        with self._lock:
            self._current_rule_text = rule_to_text(rule)
            self._current_cand_id = cand_id
        self._hyp_ready.set()

        self._fb_ready.wait()
        self._fb_ready.clear()

        with self._lock:
            tp, fp, pos_set, neg_set = self._current_fb

        return tp, fp, pos_set, neg_set

    # ------------------------------------------------------------------
    # Flower Strategy interface
    # ------------------------------------------------------------------

    def initialize_parameters(self, client_manager):
        # No numeric parameters are ever used — every round's real
        # payload (the candidate rule) travels through FitIns.config as
        # plain text, exactly like FedPopper. Only a placeholder ndarray
        # is returned here to satisfy Flower's API.
        return ndarrays_to_parameters([np.array([], dtype="<U1")])

    def configure_fit(self, server_round, parameters, client_manager):
        if self.early_stop:
            raise EarlyStopSignal(
                f"FedMDL loop finished before round {server_round}; "
                "stopping the Flower server now."
            )

        self.last_round = server_round
        available = client_manager.num_available()
        sample_size, min_num_clients = self.num_fit_clients(available)

        clients = client_manager.sample(
            num_clients=sample_size, min_num_clients=min_num_clients
        )

        if self.learning_start is None:
            now = self.timer()
            self.startup_time = now - self.global_start
            self.learning_start = now

        if self.num_pos_global is None:
            # Registration round: no real candidate exists yet (the
            # background thread is blocked on `_registration_ready`), so
            # ask every client only for its local example counts.
            config = {"round": server_round, "phase": "register"}
        else:
            # Wait for the background thread to have a real candidate
            # ready — unblocks almost immediately except on round 1
            # right after registration, when the thread still needs to
            # build its Generator.
            self._hyp_ready.wait()
            self._hyp_ready.clear()

            # The background thread also sets `_hyp_ready` once the whole
            # procedure (search, signature round, combine) is over.
            if self.early_stop:
                raise EarlyStopSignal(
                    f"FedMDL finished before round {server_round}; "
                    "stopping the Flower server now."
                )

            if self._search_done and not self._sig_round_sent:
                # Last round: ask for the signature tables over the pool.
                self._sig_round_sent = True
                config = {
                    "round": server_round,
                    "phase": "signatures",
                    "pool": json.dumps(self._sig_pool_ids),
                }
            else:
                with self._lock:
                    rule_text = self._current_rule_text
                    cand_id = self._current_cand_id
                config = {
                    "round": server_round,
                    "phase": "test",
                    "rule": rule_text,
                    "cand_id": cand_id,
                    "mode": self.combine_mode,
                }

        return [(c, FitIns(parameters, config)) for c in clients]

    def _reject_round_and_continue(self):
        """Mirrors FedPopper's _reject_round_and_continue: keep the
        background thread synchronized on a failed/incomplete Flower
        round without recording any (false) coverage for the current
        candidate."""
        if self._sig_round_sent and not self._sig_ready.is_set():
            # The signature round itself failed: no combine is possible.
            self._sig_tables = None
            self._sig_ready.set()
            return
        with self._lock:
            self._current_fb = (0, 0, frozenset(), frozenset())
        self._fb_ready.set()

    def aggregate_fit(self, server_round, results, failures):
        log(INFO, f"[Round {server_round}] results={len(results)} failures={len(failures)}")

        if not results or (not self.accept_failures and failures):
            if self.num_pos_global is not None:
                self._reject_round_and_continue()
            return ndarrays_to_parameters([np.array([], dtype="<U1")]), {}

        if self.num_pos_global is None:
            # Registration round: every client reports its local counts
            # via metrics; once we have all of them, assign global offsets
            # and let the background thread start generating.
            counts_by_client = {}
            for client, res in results:
                client_id = str(res.metrics.get("client_id", client.cid))
                num_pos_local = int(res.metrics.get("num_pos", 0))
                num_neg_local = int(res.metrics.get("num_neg", 0))
                counts_by_client[client_id] = (num_pos_local, num_neg_local)

            if len(counts_by_client) < self.min_fit_clients:
                log(
                    WARNING,
                    f"[Round {server_round}] Incomplete registration: "
                    f"{len(counts_by_client)}/{self.min_fit_clients} clients.",
                )
                return ndarrays_to_parameters([np.array([], dtype="<U1")]), {}

            self._register_client_counts(counts_by_client)
            return ndarrays_to_parameters([np.array([], dtype="<U1")]), {}

        if self._sig_round_sent and not self._sig_ready.is_set():
            # Signature round: sum the clients' tables (counts per
            # signature) into one global pair of tables.
            pos_tables, neg_tables = [], []
            for client, res in results:
                client_id = str(res.metrics.get("client_id", client.cid))
                if client_id not in self._client_pos_offset:
                    log(WARNING, f"[Round {server_round}] Unregistered client {client_id}, skipping.")
                    continue
                pos_tables.append(json.loads(res.metrics.get("pos_sig", "[]")))
                neg_tables.append(json.loads(res.metrics.get("neg_sig", "[]")))
            self._sig_tables = (merge_tables(pos_tables), merge_tables(neg_tables))
            self._sig_ready.set()
            return ndarrays_to_parameters([np.array([], dtype="<U1")]), {}

        # Normal round: gather the clients' answers for the candidate just
        # tested.
        #  - "indices": each client says which of ITS examples are covered
        #    (local positions); the server maps them to global positions
        #    with the offsets of the inventory. It never sees the examples.
        #  - "signatures": each client only sends two counts.
        tp_global = 0
        fp_global = 0
        pos_global: set = set()
        neg_global: set = set()

        for client, res in results:
            client_id = str(res.metrics.get("client_id", client.cid))
            if client_id not in self._client_pos_offset:
                # A client that joined after registration — its examples
                # were never counted into the global inventory, so its
                # feedback can't be placed correctly. Skip it.
                log(WARNING, f"[Round {server_round}] Unregistered client {client_id}, skipping.")
                continue

            if self.combine_mode == "indices":
                pos_off = self._client_pos_offset[client_id]
                neg_off = self._client_neg_offset[client_id]
                pos_global |= {pos_off + i for i in json.loads(res.metrics.get("pos_covered", "[]"))}
                neg_global |= {neg_off + i for i in json.loads(res.metrics.get("neg_covered", "[]"))}
            else:
                tp_global += int(res.metrics.get("pos_count", 0))
                fp_global += int(res.metrics.get("neg_count", 0))

        if self.combine_mode == "indices":
            tp_global, fp_global = len(pos_global), len(neg_global)
            fb = (tp_global, fp_global, frozenset(pos_global), frozenset(neg_global))
        else:
            fb = (tp_global, fp_global, None, None)

        fb_start = self.timer()
        with self._lock:
            self._current_fb = fb
        self._fb_ready.set()
        self.t_federation += self.timer() - fb_start

        # Do NOT also wait on `_hyp_ready` here. The background thread
        # sets it exactly once per candidate (inside `_send_and_wait`),
        # and the NEXT round's `configure_fit` is the one that consumes
        # it to fetch that candidate. Waiting on it here too would steal
        # that same single `set()` before `configure_fit` ever sees it —
        # a real deadlock this exact mistake caused during testing:
        # `aggregate_fit` would consume the signal meant for round N+1's
        # `configure_fit`, which would then block forever on a `.wait()`
        # that nothing is ever going to `.set()` again until a candidate
        # AFTER that one is generated — which itself never happens,
        # because that generation only resumes once round N+1 has run.
        return ndarrays_to_parameters([np.array([], dtype="<U1")]), {
            "pool_size": self.pool_size,
            "candidates_tested": self.total_candidates_tested,
        }

    def configure_evaluate(self, server_round, parameters, client_manager):
        return []  # no separate evaluation phase — see FedPopper's own
        # rationale for disabling this (fraction_evaluate=0.0 by default)

    def aggregate_evaluate(self, server_round, results, failures):
        if not results:
            return None, {}
        num_examples = sum(r.num_examples for _, r in results)
        if num_examples == 0:
            return None, {}
        loss_aggregated = weighted_loss_avg([(r.num_examples, r.loss) for _, r in results])
        return loss_aggregated, {}

    def evaluate(self, server_round, parameters):
        return None

    def num_fit_clients(self, num_available_clients):
        num_clients = int(num_available_clients * self.fraction_fit)
        return max(num_clients, self.min_fit_clients), self.min_available_clients

    def num_evaluation_clients(self, num_available_clients):
        num_clients = int(num_available_clients * self.fraction_evaluate)
        return max(num_clients, self.min_evaluate_clients), self.min_available_clients
