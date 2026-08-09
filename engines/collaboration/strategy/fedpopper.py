#working fedpopper.py 
from typing import Dict, List, Optional, Tuple
from logging import WARNING, INFO, DEBUG
from flwr.common.logger import log
from flwr.common import (
    EvaluateIns,
    EvaluateRes,
    FitIns,
    FitRes,
    MetricsAggregationFn,
    NDArrays,
    Parameters,
    Scalar,
    ndarrays_to_parameters,
    parameters_to_ndarrays,
)

import json
from logging import WARNING
from typing import Callable, Dict, List, Optional, Tuple, Union
from flwr.server.client_manager import ClientManager
from flwr.server.client_proxy import ClientProxy
from flwr.server.strategy.aggregate import aggregate, weighted_loss_avg
from flwr.server.strategy import Strategy

import time
from popper.loop import Outcome, build_rules, ground_rules, build_rules_server
from popper.core import Clause
from popper.asp import ClingoGrounder, ClingoSolver
from popper.generate import generate_program
from popper.constrain import Constrain
from popper.federatedtester import FederatedTester
from popper.util import Settings, Stats

import numpy as np
import threading
import logging
WARNING_MIN_AVAILABLE_CLIENTS_TOO_LOW = """
Setting `min_available_clients` lower than `min_fit_clients` or
`min_evaluate_clients` can cause the server to fail when there are too few clients
connected to the server. `min_available_clients` must be set to a value larger
than or equal to the values of `min_fit_clients` and `min_evaluate_clients`.
"""
logging.basicConfig(level=logging.INFO)


OUTCOME_ENCODING = {"all": 1, "some": 2, "none": 3}
OUTCOME_DECODING = {1: "all", 2: "some", 3: "none"}

AGG_TABLE_POS = {
    ("all","all"): "all",
    ("all","some"): "some",
    ("all","none"): "some",
    ("some","some"): "some",
    ("some","none"): "some",
    ("none","none"): "none",
}

AGG_TABLE_NEG = {
    ("some","some"): "some",
    ("some","none"): "some",
    ("none","some"): "some",
    ("none","none"): "none",
}


# ------------------------------------------------------
#   OUTCOME AGGREGATION
# ------------------------------------------------------

def aggregate_outcomes(outcomes):
    """
    outcomes: list of tuples ('all'/'some'/'none', 'all'/'some'/'none')
    Returns aggregated (E+, E-)
    """

    if len(outcomes) == 0:
        return ("none","none")

    Eplus, Eminus = outcomes[0]

    for (ep, em) in outcomes[1:]:
        # positive
        Eplus = AGG_TABLE_POS.get((Eplus, ep), Eplus)
        # negative
        Eminus = AGG_TABLE_NEG.get((Eminus, em), Eminus)

    return (Eplus, Eminus)



class FedPopper(Strategy):

    def __init__(
    self,
    settings,
    stats=None,
    solver=None,
    grounder=None,
    constrainer=None,
    tester=None,
    fraction_fit: float = 1.0,
    fraction_evaluate: float = 1.0,
    min_fit_clients: int = 2,
    min_evaluate_clients: int = 2,
    min_available_clients: int = 2,
    fit_metrics_aggregation_fn=None,
    accept_failures: bool = False,
    
    ):
        super().__init__()

        if (
            min_fit_clients > min_available_clients
            or min_evaluate_clients > min_available_clients
        ):
            log(WARNING, WARNING_MIN_AVAILABLE_CLIENTS_TOO_LOW)

        self.settings    = settings
        self.solver      = solver      if solver      is not None else ClingoSolver(settings)
        self.grounder    = grounder    if grounder    is not None else ClingoGrounder()
        self.constrainer = constrainer if constrainer is not None else Constrain()
        self.tester      = tester      if tester      is not None else FederatedTester()
        self.stats       = stats       if stats       is not None else Stats(log_best_programs=settings.info)

        self.fraction_fit          = fraction_fit
        self.fraction_evaluate     = fraction_evaluate
        self.min_fit_clients       = min_fit_clients
        self.min_evaluate_clients  = min_evaluate_clients
        self.min_available_clients = min_available_clients
        self.fit_metrics_aggregation_fn = fit_metrics_aggregation_fn
        self.accept_failures = accept_failures

        self.best_score      = None
        self.best_hypothesis = None
        self.solution_params = None
        self.early_stop      = False
        self.startup_time = None
        self.learning_start = None
        self.learning_time = None

        self._hyp_ready   = threading.Event()
        self._fb_ready    = threading.Event()
        self._lock        = threading.Lock()
        self._current_hyp = None
        self._current_fb  = None
        self.with_suspension = True  # True = wall-clock, False = CPU time
        self.timer = time.perf_counter if self.with_suspension else time.process_time

        self.tFedPopper = 0.0
        self.tCentralPopper = 0.0
        self.global_start = self.timer()
        self.performance_summary_printed = False
        self._popper_thread = threading.Thread(
            target=self._popper_loop,
            daemon=True,
            name="PopperLoop"
        )
        self.last_round = 0
        self._popper_thread.start()

    def __repr__(self):
        return "FedPopper"
    
    def _print_performance_summary(self, force=False):
        if self.performance_summary_printed and not force:
            return

        global_time = self.timer() - self.global_start

        print("\n========== PERFORMANCE SUMMARY ==========", flush=True)
        print(f"Total time              : {global_time:.4f}s", flush=True)
        print(f"Time in Popper core     : {self.tCentralPopper:.4f}s", flush=True)
        print(f"Time in Federation      : {self.tFedPopper:.4f}s", flush=True)
        print(
            f"Startup time            : "
            f"{float(self.startup_time or 0.0):.4f}s",
            flush=True,
            )

        print(
            f"Learning time           : "
            f"{float(self.learning_time or 0.0):.4f}s",
            flush=True,
        )

        if global_time > 0:
            print(f"Coordination ratio      : {self.tFedPopper/global_time:.2%}", flush=True)
        else:
            print("Coordination ratio      : N/A", flush=True)

        self.performance_summary_printed = True
    # ------------------------------------------------------------------
    # POPPER LOOP — exactement run_server() de srvpopper.py
    # Tourne dans un thread séparé.
    # Remplace federated_test() par _send_and_wait()
    # ------------------------------------------------------------------
    def _popper_loop(self):
        import time
        wall_start = time.perf_counter()
        TIMEOUT = 600

        #best_score = None

        try:
            for size in range(1, self.settings.max_literals + 1):

                self.stats.update_num_literals(size)
                self.solver.update_number_of_literals(size)

                while True:

                    # TIMEOUT
                    if time.perf_counter() - wall_start > TIMEOUT:
                        log(INFO, "TIMEOUT reached.")
                        self.early_stop = True
                        self._hyp_ready.set()
                        return

                    # GENERATE
                    with self.stats.duration('generate'):
                        model = self.solver.get_model()
                        if not model:
                            break
                        program, before, min_clause = generate_program(model)
                        self.stats.total_programs += 1

                    # FEDERATED TEST — envoie hypothèse, attend feedback

                    with self._lock:
                        self._current_hyp = program
                        self._current_before = before
                        self._current_min_clause = min_clause

                    start_fed = self.timer()
                    #outcome, fed_score = self._send_and_wait(program)
                    (outcome,fed_score,inconsistent_rules,totally_incomplete_rules,) = self._send_and_wait(program)
                    self.tFedPopper += self.timer() - start_fed
                    
                    log(INFO, f"outcome={outcome}, score={fed_score}")

                    

                    # UPDATE BEST
                    if self.best_score is None or fed_score > self.best_score:
                        self.best_score = fed_score
                        self.best_hypothesis = program

                    # STOP CONDITION
                    if outcome == ("all", "none"):
                        log(INFO, "Solution found (ALL, NONE)!")
                        rules_arr = np.array(
                            [Clause.to_code(r) for r in program],
                            dtype="<U1000"
                        )
                        self.solution_params = ndarrays_to_parameters([rules_arr])
                        self.early_stop = True
                        self._hyp_ready.set()  # débloque configure_fit
                       
                        return

                    # BUILD / GROUND / ADD
                    start_symb = self.timer()
                    with self.stats.duration('build'):
                        #rules = build_rules(
                        #    self.settings, self.stats, self.constrainer,
                        #    self.tester, program, before, min_clause, outcome
                        #)
                        rules = build_rules_server(
                            self.settings,
                            self.stats,
                            self.constrainer,
                            self.tester,
                            program,
                            before,
                            min_clause,
                            outcome,
                            inconsistent_rules,
                            totally_incomplete_rules,
                        )
                    #start_symb = self.timer()
                    #with self.stats.duration('build'):
                    #    rules = build_rules(
                    #        self.settings, self.stats, self.constrainer,
                    #        self.tester, program, before, min_clause, outcome
                    #    )
                        
                        # ── NOUVEAU ──────────────────────────────────────────────
                        # is_totally_incomplete est déjà encodé dans outcome NONE+
                        # On peut l'exploiter sans information supplémentaire
                    #    positive_outcome, negative_outcome = outcome
                    #    if positive_outcome == Outcome.NONE:
                    #        for rule in program:
                    #            if Clause.is_separable(rule):
                    #                rules.update(
                    #                    self.constrainer.redundancy_constraint(
                    #                        [rule], before, min_clause
                    #                   )
                    #                )
                        # ── FIN NOUVEAU ──────────────────────────────────────────

                    with self.stats.duration('ground'):
                        rules = ground_rules(
                            self.stats, self.grounder,
                            self.solver.max_clauses, self.solver.max_vars,
                            rules
                        )

                    with self.stats.duration('add'):
                        self.solver.add_ground_clauses(rules)

                    self.tCentralPopper += self.timer() - start_symb

        except Exception as e:
            log(WARNING, f"Popper loop error: {e}")
            import traceback; traceback.print_exc()

        # Recherche exhaustée
        log(INFO, "Search exhausted.")
        self.early_stop = True
        self._hyp_ready.set()

    def _send_and_wait(self, program):
        """
        Envoie l'hypothèse au thread Flower et attend le feedback.
        Equivalent de federated_test() dans srvpopper.
        """
        # Stocker l'hypothèse pour configure_fit
        with self._lock:
            self._current_hyp = program

        # Signaler à Flower qu'une nouvelle hypothèse est prête
        self._hyp_ready.set()

        # Attendre le feedback de aggregate_fit
        self._fb_ready.wait()
        self._fb_ready.clear()

        with self._lock:
            (
                outcome,
                fed_score,
                inconsistent_rules,
                totally_incomplete_rules,
            ) = self._current_fb

        return (
            outcome,
            fed_score,
            inconsistent_rules,
            totally_incomplete_rules,
        )

    # ------------------------------------------------------------------
    # initialize_parameters — envoie rien, Popper génère H0 tout seul
    # ------------------------------------------------------------------
    def initialize_parameters(self, client_manager):
        log(INFO, "Waiting for H0 from Popper loop...")

        # Attendre que le thread Popper génère H0
        self._hyp_ready.wait()
        self._hyp_ready.clear()

        if self.early_stop:
            return ndarrays_to_parameters([np.array([], dtype="<U1000")])

        with self._lock:
            program = self._current_hyp

        log(INFO, f"H0 ready ({len(program)} clause(s)):")
        for r in program:
            log(INFO, f"  {Clause.to_code(r)}")

        rules_arr = np.array(
            [Clause.to_code(r) for r in program],
            dtype="<U1000"
        )
        return ndarrays_to_parameters([rules_arr])

    # ------------------------------------------------------------------
    # configure_fit — envoie l'hypothèse courante aux clients
    # ------------------------------------------------------------------

    def configure_fit(self, server_round, parameters, client_manager):
        
        if self.early_stop:
            return []
        self.last_round = server_round
        available = client_manager.num_available()
        sample_size, min_num_clients = self.num_fit_clients(available)

        log(INFO, f"[Round {server_round}] available clients = {available}")
        log(INFO, f"[Round {server_round}] sampling {sample_size} clients, min required = {min_num_clients}")

        clients = client_manager.sample(
            num_clients=sample_size,
            min_num_clients=min_num_clients,
        )

        if self.learning_start is None:
            now = self.timer()

            self.startup_time = now - self.global_start
            self.learning_start = now

            print(
                f"[Timing] All required clients ready after "
                f"{self.startup_time:.4f}s",
                flush=True,
            )

        log(INFO, f"[Round {server_round}] selected clients = {[c.cid for c in clients]}")

        return [
            (c, FitIns(parameters, {"round": server_round}))
            for c in clients
        ]
    def configure_fitold(self, server_round, parameters, client_manager):
        if self.early_stop:
            return []

        sample_size, min_num_clients = self.num_fit_clients(
            client_manager.num_available()
        )
        clients = client_manager.sample(
            num_clients=sample_size,
            min_num_clients=min_num_clients,
        )

        return [
            (c, FitIns(parameters, {"round": server_round}))
            for c in clients
        ]
    
    def _reject_round_and_continue(self, fed_score: float = 0.0):
        """Reject a partial/failed Flower round while keeping Popper synchronized."""

        with self._lock:
            #self._current_fb = (("none", "some"), fed_score)
            program_length = len(self._current_hyp or [])

            self._current_fb = (
                ("none", "some"),
                fed_score,
                [False] * program_length,
                [False] * program_length,
            )

        self._fb_ready.set()

        self._hyp_ready.wait()
        self._hyp_ready.clear()

        if self.early_stop:
            if self.solution_params:
                return self.solution_params, {"fed_score": fed_score}

            if self.best_hypothesis:
                rules_arr = np.array(
                    [Clause.to_code(r) for r in self.best_hypothesis],
                    dtype="<U1000"
                )
                self.solution_params = ndarrays_to_parameters([rules_arr])
            else:
                self.solution_params = ndarrays_to_parameters(
                    [np.array([], dtype="<U1000")]
                )

            return self.solution_params, {"fed_score": fed_score}

        with self._lock:
            program = self._current_hyp

        rules_arr = np.array(
            [Clause.to_code(r) for r in program],
            dtype="<U1000"
        )
        return ndarrays_to_parameters([rules_arr]), {"fed_score": fed_score}
    # ------------------------------------------------------------------
    # aggregate_fit — collecte feedback clients, le passe au thread Popper
    #                 puis attend la prochaine hypothèse
    # ------------------------------------------------------------------
    #def aggregate_fit(self, server_round, results, failures):

    def aggregate_fit(
    self,
    server_round: int,
    results,
    failures,
):
        log(INFO, f"[Round {server_round}] results={len(results)} failures={len(failures)}")

        if not results:
            log(WARNING, f"[Round {server_round}] No results.")
            return self._reject_round_and_continue(0.0)

        if not self.accept_failures and failures:
            log(WARNING, f"[Round {server_round}] Failures detected and not accepted.")
            return self._reject_round_and_continue(0.0)

        if len(results) < self.min_fit_clients:
            log(WARNING, (
                f"[Round {server_round}] Incomplete round: expected at least "
                f"{self.min_fit_clients} results, got {len(results)}"
            ))
            return self._reject_round_and_continue(0.0)

        epsilons = []
        scores = []
        client_inconsistent_feedbacks = []
        client_totally_incomplete_feedbacks = []

        for client, res in results:
            inconsistent_rules = json.loads(
                res.metrics.get("inconsistent_rules", "[]")
            )

            totally_incomplete_rules = json.loads(
                res.metrics.get("totally_incomplete_rules", "[]")
            )

            log(
                INFO,
                f"[Round {server_round}] client {client.cid} "
                f"inconsistent_rules={inconsistent_rules}",
            )

            log(
                INFO,
                f"[Round {server_round}] client {client.cid} "
                f"totally_incomplete_rules={totally_incomplete_rules}",
            )

            client_inconsistent_feedbacks.append(inconsistent_rules)
            client_totally_incomplete_feedbacks.append(
                totally_incomplete_rules
)




            arrs = parameters_to_ndarrays(res.parameters)
            if not arrs or len(arrs[0]) < 2:
                log(WARNING, f"[Round {server_round}] Invalid payload from client {client.cid}")
                continue

            vals = arrs[0].tolist()
            e_pos = int(vals[0])
            e_neg = int(vals[1])
            score = float(vals[2]) if len(vals) >= 3 else 0.0

            if e_pos not in OUTCOME_DECODING or e_neg not in OUTCOME_DECODING:
                log(WARNING, f"[Round {server_round}] Invalid outcome encoding from client {client.cid}: {vals}")
                continue

            eps = (OUTCOME_DECODING[e_pos], OUTCOME_DECODING[e_neg])
            epsilons.append(eps)
            scores.append(score)

            log(INFO, f"[Round {server_round}] client {client.cid} -> outcome={eps}, score={score}")

        if len(epsilons) < self.min_fit_clients:
            log(WARNING, (
                f"[Round {server_round}] Not enough valid client payloads after parsing: "
                f"{len(epsilons)}"
            ))
            return self._reject_round_and_continue(0.0)
        
        aggregated_inconsistent_rules = [
            any(client_values)
            for client_values in zip(*client_inconsistent_feedbacks)
        ]

        aggregated_totally_incomplete_rules = [
            all(client_values)
            for client_values in zip(
                *client_totally_incomplete_feedbacks
            )
        ]

        log(
            INFO,
            f"[Round {server_round}] aggregated inconsistent rules="
            f"{aggregated_inconsistent_rules}",
        )

        log(
            INFO,
            f"[Round {server_round}] aggregated totally incomplete rules="
            f"{aggregated_totally_incomplete_rules}",
        )
        outcome = aggregate_outcomes(epsilons)
        fed_score = sum(scores)

        log(INFO, f"[Round {server_round}] aggregated outcome={outcome}, fed_score={fed_score}")

        with self._lock:
            #self._current_fb = (outcome, fed_score)
            self._current_fb = (
                outcome,
                fed_score,
                aggregated_inconsistent_rules,
                aggregated_totally_incomplete_rules,
            )

        self._fb_ready.set()

        self._hyp_ready.wait()
        self._hyp_ready.clear()

        if self.early_stop:
            # Stop learning timer
            end_time = self.timer()

            if self.learning_start is not None:
                self.learning_time = end_time - self.learning_start
            else:
                self.learning_time = 0.0

            print(
                f"[Timing] Learning time: "
                f"{self.learning_time:.4f}s",
                flush=True,
            )

            if self.solution_params:
                return self.solution_params, {"fed_score": fed_score}

            if self.best_hypothesis:
                rules_arr = np.array(
                    [Clause.to_code(r) for r in self.best_hypothesis],
                    dtype="<U1000"
                )
                self.solution_params = ndarrays_to_parameters([rules_arr])
            else:
                self.solution_params = ndarrays_to_parameters(
                    [np.array([], dtype="<U1000")]
                )

            return self.solution_params, {"fed_score": fed_score}

        with self._lock:
            program = self._current_hyp

        rules_arr = np.array(
            [Clause.to_code(r) for r in program],
            dtype="<U1000"
        )
        return ndarrays_to_parameters([rules_arr]), {"fed_score": fed_score}


    # ------------------------------------------------------------------
    # configure_evaluate
    # ------------------------------------------------------------------
    def configure_evaluate(self, server_round, parameters, client_manager):
        if self.early_stop:
            return []
        if self.fraction_evaluate == 0.0:
            return []

        params_for_eval = self.solution_params or parameters

        sample_size, min_num_clients = self.num_evaluation_clients(
            client_manager.num_available()
        )
        clients = client_manager.sample(
            num_clients=sample_size,
            min_num_clients=min_num_clients,
        )
        return [(c, EvaluateIns(params_for_eval, {})) for c in clients]

    # ------------------------------------------------------------------
    # aggregate_evaluate
    # ------------------------------------------------------------------
    def aggregate_evaluate(self, server_round, results, failures):
        if not results:
            return None, {}

        num_examples = sum(r.num_examples for _, r in results)
        if num_examples == 0:
            return None, {}

        loss_aggregated = weighted_loss_avg(
            [(r.num_examples, r.loss) for _, r in results]
        )
        return loss_aggregated, {}

    def evaluate(self, server_round, parameters):
        return None

    def num_fit_clients(self, num_available_clients):
        num_clients = int(num_available_clients * self.fraction_fit)
        return max(num_clients, self.min_fit_clients), self.min_available_clients

    def num_evaluation_clients(self, num_available_clients):
        num_clients = int(num_available_clients * self.fraction_evaluate)
        return max(num_clients, self.min_evaluate_clients), self.min_available_clients