# srvpopper.py
# ------------------------------------------------------
#   FILP Distributed Server using BLPy protocol
# ------------------------------------------------------

import os
import re
import socket
import time

from popper.asp import ClingoSolver, ClingoGrounder
from popper.constrain import Constrain
from popper.core import Clause
from popper.federatedtester import FederatedTester
from popper.util import load_kbpath, Settings, Stats
from popper.loop import build_rules_server, ground_rules
from popper.generate import generate_program

from .strategy.aggstrategy import aggregate_outcomes

# ======================================================
#  SERVER CONFIGURATION
# ======================================================

import argparse


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "..",
    )
)

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start the Bach4Popper coordination server."
    )

    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to the global dataset directory.",
    )

    parser.add_argument(
        "--clients",
        type=int,
        required=True,
        help="Number of expected coordination clients.",
    )

    parser.add_argument(
        "--rounds",
        type=int,
        default=35000,
        help="Maximum number of learning rounds.",
    )

    parser.add_argument(
        "--store-address",
        type=str,
        default="127.0.0.1:8000",
        help="Bach coordination store address.",
    )

    return parser.parse_args()


def resolve_dataset_path(
    dataset_argument: str,
) -> str:
    if os.path.isabs(dataset_argument):
        dataset_path = dataset_argument
    else:
        dataset_path = os.path.join(
            PROJECT_ROOT,
            dataset_argument,
        )

    dataset_path = os.path.abspath(
        dataset_path
    )

    if not os.path.isdir(dataset_path):
        raise FileNotFoundError(
            f"Server dataset directory not found: {dataset_path}"
        )

    return dataset_path


def parse_address(
    address: str,
) -> tuple[str, int]:
    host, port = address.rsplit(
        ":",
        1,
    )

    return host, int(port)
# ======================================================
#  GLOBAL STATE
# ======================================================

class FILPServerState:
    """
    Preserve the complete Popper solver state
    between federated rounds.
    """

    def __init__(
        self,
        settings,
        solver,
        grounder,
        constrainer,
        tester,
        stats,
        min_clause,
        before,
        clause_size,
        hypothesis,
    ):
        self.settings = settings
        self.solver = solver
        self.grounder = grounder
        self.constrainer = constrainer
        self.tester = tester
        self.stats = stats

        self.current_hypothesis = hypothesis
        self.current_before = before
        self.current_min_clause = min_clause
        self.current_clause_size = clause_size


# ======================================================
#  UI
# ======================================================

def cli_prompt():

    banner = r"""
   _____               ____
  / ___/______   __   / __ \____  ____  ____  ___  _____
  \__ \/ ___/ | / /  / /_/ / __ \/ __ \/ __ \/ _ \/ ___/
 ___/ / /   | |/ /  / ____/ /_/ / /_/ / /_/ /  __/ /
/____/_/    |___/  /_/    \____/ .___/ .___/\___/_/
                               /_/   /_/
"""

    print(banner)


# ======================================================
#  INITIALISATION
# ======================================================


def popper_initialisation(path_dir):

    print(
        "Initialising Distributed FILP..."
    )

    # Server loads only the bias.
    _, _, bias_file = load_kbpath(
        path_dir
    )

    settings = Settings(
        bias_file,
        None,
        None,
    )

    stats = Stats(
        log_best_programs=settings.info
    )

    solver = ClingoSolver(
        settings
    )

    grounder = ClingoGrounder()

    constrainer = Constrain()

    tester = FederatedTester(
        settings
    )

    current_hypothesis = None
    current_before = None
    current_min_clause = 0
    current_clause_size = 0

    state = FILPServerState(
        settings=settings,
        solver=solver,
        grounder=grounder,
        constrainer=constrainer,
        tester=tester,
        stats=stats,
        min_clause=current_min_clause,
        before=current_before,
        clause_size=current_clause_size,
        hypothesis=current_hypothesis,
    )

    return state


# ======================================================
#  STORE HELPERS
# ======================================================

def reset_store(store):

    print("Resetting STORE")

    store.send(
        b"reset"
    )

    store.recv(
        1024
    )


def normalize_rule_for_store(
    rule_str,
):
    """
    Transform a Popper rule into a clean representation
    suitable for the coordination store.
    """

    rule = (
        rule_str
        .replace("{", "")
        .replace("}", "")
        .strip()
    )

    if rule.endswith("."):
        rule = rule[:-1]

    rule = rule.replace(
        ";",
        ",",
    )

    if ":-" in rule:

        head, body = rule.split(
            ":-",
            1,
        )

        rule = (
            f"{head.strip()} :- "
            f"{body.strip()}"
        )

    else:
        rule = rule.strip()

    if not rule.endswith("."):
        rule += "."

    return rule


# ======================================================
#  SEND HYPOTHESIS TO CLIENTS
# ======================================================

def tell_hypothesis(
    store,
    hypothesis,
    tour,
):

    number_of_clauses = len(
        hypothesis
    )

    # --------------------------------------------------
    # Number of clauses
    # --------------------------------------------------

    message = (
        f"tell(prgmlen("
        f"{tour},"
        f"{number_of_clauses}"
        f"))"
    )

    print(
        "Sending:",
        message,
    )

    store.send(
        message.encode()
    )

    store.recv(
        1024
    )

    # --------------------------------------------------
    # Clauses
    # --------------------------------------------------

    for clause_index, clause in enumerate(
        hypothesis
    ):

        clean_clause = clause.strip()

        payload = (
            "{"
            + clean_clause
            + "}"
        )

        message = (
            f"tell(prgm("
            f"{tour},"
            f"{clause_index},"
            f"{payload}"
            f"))"
        )

        print(
            "Sending:",
            message,
        )

        store.send(
            message.encode()
        )

        store.recv(
            1024
        )


# ======================================================
#  EPSILON FEEDBACK
# ======================================================

def get_epsilon_pairs(
    store,
    nb_client,
    tour,
):

    epsilon_pairs = []

    print(
        f"nb_client = {nb_client}"
    )

    for client_id in range(
        1,
        nb_client + 1,
    ):

        while True:

            message = (
                f"ask(epair("
                f"{tour},"
                f"{client_id}"
                f"))"
            )

            store.send(
                message.encode("utf-8")[:1024]
            )

            response = (
                store.recv(1024)
                .decode("utf-8")
                .strip()
            )

            print(
                "Response from store:",
                response,
            )

            if (
                "wait" in response
                or "failed" in response
            ):
                time.sleep(
                    0.05
                )

                continue

            epsilon_pairs.append(
                response
            )

            break

    return epsilon_pairs


def parse_epair_with_score(
    response,
):
    """
    Expected:

        epair(
            round,
            client,
            Eplus,
            Eminus,
            score
        )
    """

    if (
        not response
        or "(" not in response
        or ")" not in response
    ):
        return (
            "none",
            "none",
            0.0,
        )

    inner = response[
        response.find("(") + 1:
        response.rfind(")")
    ]

    parts = [
        part.strip().lower()
        for part in inner.split(",")
    ]

    if len(parts) >= 5:

        epsilon_positive = parts[2]
        epsilon_negative = parts[3]

        try:
            score = float(
                parts[4]
            )

        except Exception:
            score = 0.0

        return (
            epsilon_positive,
            epsilon_negative,
            score,
        )

    # Backward compatibility
    if len(parts) >= 4:

        return (
            parts[2],
            parts[3],
            0.0,
        )

    return (
        "none",
        "none",
        0.0,
    )


# ======================================================
#  CLAUSE-LEVEL FEEDBACK
# ======================================================

def parse_rule_feedback(
    response,
):
    """
    Expected:

        rulefb(
            round,
            client,
            clause_index,
            inconsistent,
            totally_incomplete
        )

    Returns:

        inconsistent: bool
        totally_incomplete: bool
    """

    if (
        not response
        or "(" not in response
        or ")" not in response
    ):
        raise ValueError(
            f"Invalid rule feedback: {response}"
        )

    inner = response[
        response.find("(") + 1:
        response.rfind(")")
    ]

    parts = [
        part.strip()
        for part in inner.split(",")
    ]

    if len(parts) < 5:
        raise ValueError(
            f"Invalid rule feedback: {response}"
        )

    inconsistent = bool(
        int(parts[3])
    )

    totally_incomplete = bool(
        int(parts[4])
    )

    return (
        inconsistent,
        totally_incomplete,
    )


def get_rule_feedback(
    store,
    nb_client,
    tour,
    number_of_clauses,
):
    """
    Retrieve clause-level feedback from all clients.

    Flower-equivalent aggregation:

        inconsistent(rule)
            = ANY client says inconsistent

        totally_incomplete(rule)
            = ALL clients say totally incomplete
    """

    # --------------------------------------------------
    # Feedback matrix:
    #
    # client -> [feedback clause 0, clause 1, ...]
    # --------------------------------------------------

    all_inconsistent_rules = []
    all_totally_incomplete_rules = []

    for client_id in range(
        1,
        nb_client + 1,
    ):

        client_inconsistent_rules = []
        client_totally_incomplete_rules = []

        for clause_index in range(
            number_of_clauses
        ):

            while True:

                message = (
                    f"ask(rulefb("
                    f"{tour},"
                    f"{client_id},"
                    f"{clause_index}"
                    f"))"
                )

                store.send(
                    message.encode("utf-8")[:1024]
                )

                response = (
                    store.recv(1024)
                    .decode("utf-8")
                    .strip()
                )

                print(
                    "Rule feedback from store:",
                    response,
                )

                if (
                    "wait" in response
                    or "failed" in response
                ):

                    time.sleep(
                        0.05
                    )

                    continue

                (
                    is_inconsistent,
                    is_totally_incomplete,
                ) = parse_rule_feedback(
                    response
                )

                client_inconsistent_rules.append(
                    is_inconsistent
                )

                client_totally_incomplete_rules.append(
                    is_totally_incomplete
                )

                break

        all_inconsistent_rules.append(
            client_inconsistent_rules
        )

        all_totally_incomplete_rules.append(
            client_totally_incomplete_rules
        )

    # --------------------------------------------------
    # Flower-equivalent aggregation
    # --------------------------------------------------

    if number_of_clauses == 0:

        return (
            [],
            [],
        )

    aggregated_inconsistent_rules = [
        any(client_feedback)
        for client_feedback in zip(
            *all_inconsistent_rules
        )
    ]

    aggregated_totally_incomplete_rules = [
        all(client_feedback)
        for client_feedback in zip(
            *all_totally_incomplete_rules
        )
    ]

    print(
        "[SERVER] Aggregated inconsistent rules:",
        aggregated_inconsistent_rules,
    )

    print(
        "[SERVER] Aggregated totally incomplete rules:",
        aggregated_totally_incomplete_rules,
    )

    return (
        aggregated_inconsistent_rules,
        aggregated_totally_incomplete_rules,
    )

def tell_final_hypothesis(
    store,
    hypothesis,
    tour,
):
    print(
        f"[SERVER] Publishing final hypothesis at round {tour}"
    )

    # Mark round as final
    message = (
        f"tell(prgmlen("
        f"{tour},"
        f"final"
        f"))"
    )

    print("Sending:", message)

    store.send(
        message.encode()
    )

    store.recv(
        1024
    )

    # Publish every final clause
    for clause_index, clause in enumerate(
        hypothesis
    ):
        clean_clause = clause.strip()

        payload = (
            "{"
            + clean_clause
            + "}"
        )

        message = (
            f"tell(prgm("
            f"{tour},"
            f"{clause_index},"
            f"{payload}"
            f"))"
        )

        print("Sending:", message)

        store.send(
            message.encode()
        )

        store.recv(
            1024
        )

# ======================================================
#  FEDERATED TEST
# ======================================================

def federated_test(
    program,
    store,
    nb_client,
    round_id,
):
    """
    Distributed equivalent of tester.test(program).

    The server:

        1. sends the hypothesis;
        2. receives epsilon+/epsilon-/score;
        3. receives clause-level Popper feedback;
        4. aggregates everything exactly as in FedPopper.
    """

    # --------------------------------------------------
    # Program -> strings
    # --------------------------------------------------

    rules_str = [
        normalize_rule_for_store(
            Clause.to_code(clause)
        )
        for clause in program
    ]

    # --------------------------------------------------
    # Publish hypothesis
    # --------------------------------------------------

    reset_store(
        store
    )

    store.send(
        f"tell(round({round_id}))".encode()
    )

    store.recv(
        1024
    )

    tell_hypothesis(
        store=store,
        hypothesis=rules_str,
        tour=round_id,
    )

    # --------------------------------------------------
    # Retrieve epsilon feedback
    # --------------------------------------------------

    epsilon_pairs = get_epsilon_pairs(
        store=store,
        nb_client=nb_client,
        tour=round_id,
    )

    parsed_epsilon_pairs = [
        parse_epair_with_score(
            epsilon_pair
        )
        for epsilon_pair in epsilon_pairs
    ]

    # --------------------------------------------------
    # Aggregate ALL / SOME / NONE
    # --------------------------------------------------

    outcomes = [
        (
            epsilon_positive,
            epsilon_negative,
        )
        for (
            epsilon_positive,
            epsilon_negative,
            _
        ) in parsed_epsilon_pairs
    ]

    outcome = aggregate_outcomes(
        outcomes
    )

    # --------------------------------------------------
    # Aggregate score
    # --------------------------------------------------

    scores = [
        score
        for (
            _,
            _,
            score
        ) in parsed_epsilon_pairs
    ]

    fed_score = sum(
        scores
    )

    # --------------------------------------------------
    # Retrieve and aggregate clause feedback
    # --------------------------------------------------

    (
        inconsistent_rules,
        totally_incomplete_rules,
    ) = get_rule_feedback(
        store=store,
        nb_client=nb_client,
        tour=round_id,
        number_of_clauses=len(program),
    )

    print(
        f"[SERVER] Global outcome = {outcome}"
    )

    print(
        f"[SERVER] Global score = {fed_score}"
    )

    return (
        outcome,
        fed_score,
        rules_str,
        inconsistent_rules,
        totally_incomplete_rules,
    )


# ======================================================
#  MAIN LOOP
# ======================================================

def run_server(
    with_suspension=True,
):
    tFedPopper = 0.0
    tCentralPopper = 0.0
    args = parse_arguments()

    if args.clients < 1:
        raise ValueError(
            "The number of clients must be at least 1."
        )

    nb_client = int(
        args.clients
    )

    path_dir = resolve_dataset_path(
        args.dataset
    )

    store_address = parse_address(
        args.store_address
    )

    print(
        "========== BACH4POPPER SERVER =========="
    )

    print(
        f"Dataset       : {path_dir}"
    )

    print(
        f"Clients       : {nb_client}"
    )

    print(
        f"Max rounds    : {args.rounds}"
    )

    print(
        f"Store address : {args.store_address}"
    )

    st = popper_initialisation(
        path_dir
    )

    store = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    store.connect(
        store_address
    )

    print(
        "Connected to STORE."
    )

    # --------------------------------------------------
    # Best hypothesis tracking
    # --------------------------------------------------

    best_score = None
    best_rules_str = None
    best_round = None

    round_id = 0
    found_solution = False

    TIMEOUT = 600

    # --------------------------------------------------
    # Timer selection
    # --------------------------------------------------

    timer = (
        time.perf_counter
        if with_suspension
        else time.process_time
    )

    # Timeout always uses wall-clock time.
    wall_start = time.perf_counter()

    start_time = timer()

    try:

        for size in range(
            1,
            st.settings.max_literals + 1,
        ):

            if found_solution:
                break

            st.stats.update_num_literals(
                size
            )

            st.solver.update_number_of_literals(
                size
            )

            while True:

                # ------------------------------------------
                # TIMEOUT
                # ------------------------------------------

                if (
                    time.perf_counter()
                    - wall_start
                    > TIMEOUT
                ):

                    print(
                        f"\nTIMEOUT reached "
                        f"({TIMEOUT}s)"
                    )

                    found_solution = True

                    break

                # ------------------------------------------
                # GENERATE
                # ------------------------------------------

                with st.stats.duration(
                    "generate"
                ):

                    model = (
                        st.solver.get_model()
                    )

                    if not model:
                        break

                    (
                        program,
                        before,
                        min_clause,
                    ) = generate_program(
                        model
                    )

                # ------------------------------------------
                # FEDERATED TEST
                # ------------------------------------------

                start_fed = timer()

                with st.stats.duration(
                    "test"
                ):

                    (
                        outcome,
                        score,
                        rules_str,
                        inconsistent_rules,
                        totally_incomplete_rules,
                    ) = federated_test(
                        program=program,
                        store=store,
                        nb_client=nb_client,
                        round_id=round_id,
                    )

                tFedPopper += (
                    timer()
                    - start_fed
                )

                st.stats.total_programs += 1

                print(
                    f"[Program #{round_id}] "
                    f"outcome={outcome}, "
                    f"score={score}"
                )

                print(
                    "[Program feedback] "
                    f"inconsistent="
                    f"{inconsistent_rules}, "
                    f"totally_incomplete="
                    f"{totally_incomplete_rules}"
                )

                # ------------------------------------------
                # UPDATE BEST
                # ------------------------------------------

                if (
                    best_score is None
                    or score > best_score
                ):

                    best_score = score

                    best_rules_str = list(
                        rules_str
                    )

                    best_round = round_id

                # ------------------------------------------
                # STOP CONDITION
                # ------------------------------------------

                if outcome == (
                    "all",
                    "none",
                ):
                    print(
                        "\nSolution found "
                        "(ALL, NONE)"
                    )

                    final_round = round_id + 1

                    tell_final_hypothesis(
                        store=store,
                        hypothesis=rules_str,
                        tour=final_round,
                    )

                    found_solution = True
                    break

                # ------------------------------------------
                # BUILD / GROUND / ADD
                #
                # IMPORTANT:
                # Same build_rules_server() as Flower.
                # ------------------------------------------

                start_symbolic = timer()

                with st.stats.duration(
                    "build"
                ):

                    rules = build_rules_server(
                        st.settings,
                        st.stats,
                        st.constrainer,
                        st.tester,
                        program,
                        before,
                        min_clause,
                        outcome,
                        inconsistent_rules,
                        totally_incomplete_rules,
                    )

                with st.stats.duration(
                    "ground"
                ):

                    rules = ground_rules(
                        st.stats,
                        st.grounder,
                        st.solver.max_clauses,
                        st.solver.max_vars,
                        rules,
                    )

                with st.stats.duration(
                    "add"
                ):

                    st.solver.add_ground_clauses(
                        rules
                    )

                tCentralPopper += (
                    timer()
                    - start_symbolic
                )

                round_id += 1

    finally:

        try:

            store.send(
                b"close"
            )

            store.recv(
                1024
            )

        except Exception:
            pass

        store.close()

    # ==================================================
    # FINAL SUMMARY
    # ==================================================

    global_time = (
        timer()
        - start_time
    )

    print(
        "\n========== FINAL SUMMARY =========="
    )

    print(
        f"Total programs explored : "
        f"{st.stats.total_programs}"
    )

    print(
        f"Total execution time    : "
        f"{global_time:.4f}s"
    )

    if best_rules_str:

        print(
            f"\nBest hypothesis found "
            f"at round {best_round} "
            f"(score={best_score})"
        )

        for rule in best_rules_str:
            print(
                " ",
                rule,
            )

    else:

        print(
            "No valid hypothesis found."
        )

    # ==================================================
    # PERFORMANCE
    # ==================================================

    print(
        "\n========== PERFORMANCE SUMMARY =========="
    )

    print(
        f"Total time           : "
        f"{global_time:.4f}s"
    )

    print(
        f"Time in Popper core  : "
        f"{tCentralPopper:.4f}s"
    )

    print(
        f"Time in Federation   : "
        f"{tFedPopper:.4f}s"
    )

    if global_time > 0:

        print(
            f"Coordination ratio   : "
            f"{tFedPopper / global_time:.2%}"
        )

    else:

        print(
            "Coordination ratio   : N/A"
        )

    print(
        "\n========== SERVER TIMING =========="
    )

    st.stats.show()


# ======================================================
#  RUN
# ======================================================

if __name__ == "__main__":

    # Wall-clock including waiting:
    # run_server(with_suspension=True)

    # CPU-oriented execution:
    run_server(
        with_suspension=False
    )