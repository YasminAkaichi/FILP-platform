# clipopper.py
# ------------------------------------------------------
#   FILP Distributed Client using BLPy protocol
# ------------------------------------------------------

import os
import re
import socket
import traceback

from popper.tester import Tester
from popper.core import Literal
from popper.loop import decide_outcome, calc_score
from popper.util import Settings, Stats, load_kbpath


# ======================================================
#  CLIENT CONFIGURATION
# ======================================================

import argparse
from pathlib import Path


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
        description="Start a Bach4Popper coordination client."
    )

    parser.add_argument(
        "--client-id",
        type=int,
        required=True,
        help="Federated client identifier.",
    )

    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to the client's local dataset partition.",
    )

    parser.add_argument(
        "--store-address",
        type=str,
        default="127.0.0.1:8000",
        help="Bach coordination store address.",
    )

    return parser.parse_args()


def resolve_dataset_path(dataset_argument: str) -> str:
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
            f"Dataset directory not found: {dataset_path}"
        )

    return dataset_path

def parse_address(address: str) -> tuple[str, int]:
    host, port = address.rsplit(":", 1)

    return host, int(port)


# ======================================================
#  CLIENT UI
# ======================================================

def cli_prompt():
    print(
        r"""
 __ .   .__
/  `|*  [__) _ ._ ._  _ ._.
\__.||  |   (_)[_)[_)(/,[  
               |  |
"""
    )


# ======================================================
#  DATASET HELPERS
# ======================================================

def count_pos_neg_in_file(ex_file: str):
    pos = 0
    neg = 0

    with open(ex_file, "r") as file:
        for line in file:
            stripped = line.strip()

            if stripped.startswith("pos("):
                pos += 1

            elif stripped.startswith("neg("):
                neg += 1

    return pos, neg


def initialisation(
    client_id: int,
    path_dir: str,
):
    print("Initialising client...")

    bk_file, ex_file, bias_file = load_kbpath(
        path_dir
    )

    settings = Settings(
        bias_file,
        ex_file,
        bk_file,
    )

    tester = Tester(
        settings
    )

    stats = Stats(
        log_best_programs=settings.info
    )

    settings.num_pos = len(
        tester.pos
    )

    settings.num_neg = len(
        tester.neg
    )

    file_pos, file_neg = (
        count_pos_neg_in_file(
            ex_file
        )
    )

    print(
        f"[CLIENT {client_id}] "
        f"FILE counts pos={file_pos} "
        f"neg={file_neg}"
    )

    print(
        f"[CLIENT {client_id}] "
        f"TESTER counts "
        f"pos={len(tester.pos)} "
        f"neg={len(tester.neg)}"
    )

    return (
        settings,
        tester,
        stats,
    )


# ======================================================
#  POPPER RULE PARSING
# ======================================================

def transform_rule_to_tester_format(
    rule_str: str,
):
    """
    Convert a Prolog rule received from the store into
    the representation expected by Popper's Tester.

    Example:
        f(A) :- has_car(A,B), short(B).
    """

    rule_str = rule_str.strip()

    if rule_str.endswith("."):
        rule_str = rule_str[:-1]

    if ":-" in rule_str:
        head_str, body_str = rule_str.split(
            ":-",
            maxsplit=1,
        )

        body_literals = re.findall(
            r"\w+\([^)]*\)",
            body_str,
        )

    else:
        head_str = rule_str
        body_literals = []

    head = Literal.from_string(
        head_str.strip()
    )

    body = tuple(
        Literal.from_string(
            literal.strip()
        )
        for literal in body_literals
    )

    return head, body


# ======================================================
#  CONFUSION MATRIX DISPLAY
# ======================================================

def format_conf_matrix(conf_matrix):
    tp, fn, tn, fp = conf_matrix

    precision = "n/a"

    if (tp + fp) > 0:
        precision = (
            f"{tp / (tp + fp):0.2f}"
        )

    recall = "n/a"

    if (tp + fn) > 0:
        recall = (
            f"{tp / (tp + fn):0.2f}"
        )

    accuracy = "n/a"

    total = tp + tn + fp + fn

    if total > 0:
        accuracy = (
            f"{(tp + tn) / total:0.2f}"
        )

    return (
        f"% Precision:{precision}, "
        f"Recall:{recall}, "
        f"Accuracy:{accuracy}, "
        f"TP:{tp}, FN:{fn}, "
        f"TN:{tn}, FP:{fp}\n"
    )


# ======================================================
#  LOCAL POPPER TEST
# ======================================================

def popper_test_hypothesis_final(
    hypothesis_strings,
    tester,
    stats,
):
    """
    Test the complete hypothesis locally.

    In addition to epsilon+, epsilon- and score,
    compute exactly the same clause-level feedback
    as the Flower implementation:

        is_inconsistent
        is_totally_incomplete
    """

    try:
        print(
            "\nStarting local test of hypothesis..."
        )

        print("Hypothesis strings:")

        for hypothesis_rule in hypothesis_strings:
            print(
                " ",
                hypothesis_rule,
            )

        # --------------------------------------------------
        # Parse complete hypothesis
        # --------------------------------------------------

        rules = []

        for rule_string in hypothesis_strings:
            try:
                formatted_rule = (
                    transform_rule_to_tester_format(
                        rule_string
                    )
                )

                rules.append(
                    formatted_rule
                )

            except Exception as error:
                print(
                    f"Failed to transform rule "
                    f"{rule_string}: {error}"
                )

        if not rules:
            print(
                "No valid rule could be parsed."
            )

            return (
                "none",
                "none",
                "0",
                [],
                [],
            )

        print(
            f"Total Pos examples: "
            f"{len(tester.pos)}"
        )

        print(
            f"Total Neg examples: "
            f"{len(tester.neg)}"
        )

        # --------------------------------------------------
        # Complete hypothesis evaluation
        # --------------------------------------------------

        with stats.duration("test"):
            confusion_matrix = tester.test(
                rules
            )

            # ----------------------------------------------
            # Same clause feedback as Flower
            # ----------------------------------------------

            inconsistent_rules = []
            totally_incomplete_rules = []

            for rule in rules:

                inconsistent_rules.append(
                    bool(
                        tester.is_inconsistent(
                            rule
                        )
                    )
                )

                totally_incomplete_rules.append(
                    bool(
                        tester.is_totally_incomplete(
                            rule
                        )
                    )
                )

        # --------------------------------------------------
        # Standard Popper outcome
        # --------------------------------------------------

        print(
            "Confusion matrix:",
            confusion_matrix,
        )

        print(
            format_conf_matrix(
                confusion_matrix
            )
        )

        epsilon_positive, epsilon_negative = (
            decide_outcome(
                confusion_matrix
            )
        )

        score = calc_score(
            confusion_matrix
        )

        epsilon_positive = str(
            epsilon_positive
        ).lower()

        epsilon_negative = str(
            epsilon_negative
        ).lower()

        print(
            f"Outcome = "
            f"({epsilon_positive}, "
            f"{epsilon_negative})"
        )

        print(
            f"Score = {score}"
        )

        print(
            "Inconsistent rules = "
            f"{inconsistent_rules}"
        )

        print(
            "Totally incomplete rules = "
            f"{totally_incomplete_rules}"
        )

        return (
            epsilon_positive,
            epsilon_negative,
            str(score).lower(),
            inconsistent_rules,
            totally_incomplete_rules,
        )

    except Exception:
        print(
            "Error while testing hypothesis:"
        )

        traceback.print_exc()

        return (
            "x",
            "x",
            "0",
            [],
            [],
        )


# ======================================================
#  STORE FEEDBACK
# ======================================================

def send_epair(
    sock,
    client_id,
    tour,
    epsilon_positive,
    epsilon_negative,
    score,
):
    """
    Existing Bach feedback:

        epair(
            round,
            client,
            epsilon+,
            epsilon-,
            score
        )
    """

    score_int = int(
        float(score)
    )

    message = (
        f"tell(epair("
        f"{tour},"
        f"{client_id},"
        f"{epsilon_positive},"
        f"{epsilon_negative},"
        f"{score_int}"
        f"))"
    )

    print(
        "[CLIENT] Sending:",
        message,
    )

    sock.send(
        message.encode()
    )

    response = sock.recv(
        1024
    ).decode()

    print(
        "[CLIENT] Store response:",
        response,
    )


def send_rule_feedback(
    sock,
    client_id,
    tour,
    inconsistent_rules,
    totally_incomplete_rules,
):
    """
    Send one clause-level feedback tuple per rule.

    Example:

        rulefb(
            round,
            client,
            clause_index,
            inconsistent,
            totally_incomplete
        )

    Boolean values are encoded as 0/1.
    """

    if (
        len(inconsistent_rules)
        != len(totally_incomplete_rules)
    ):
        raise ValueError(
            "Inconsistent feedback lengths: "
            f"{len(inconsistent_rules)} vs "
            f"{len(totally_incomplete_rules)}"
        )

    for clause_index, (
        is_inconsistent,
        is_totally_incomplete,
    ) in enumerate(
        zip(
            inconsistent_rules,
            totally_incomplete_rules,
        )
    ):

        inconsistent_value = int(
            bool(is_inconsistent)
        )

        incomplete_value = int(
            bool(is_totally_incomplete)
        )

        message = (
            f"tell(rulefb("
            f"{tour},"
            f"{client_id},"
            f"{clause_index},"
            f"{inconsistent_value},"
            f"{incomplete_value}"
            f"))"
        )

        print(
            "[CLIENT] Sending rule feedback:",
            message,
        )

        sock.send(
            message.encode()
        )

        response = sock.recv(
            1024
        ).decode()

        print(
            "[CLIENT] Store response:",
            response,
        )


# ======================================================
#  READ HYPOTHESIS FROM STORE
# ======================================================

def popper_read_hypothesis(
    sock,
    tour,
):
    """
    Retrieve the hypothesis generated by the Popper server
    for the current round.
    """

    # --------------------------------------------------
    # Check whether this is the final round
    # --------------------------------------------------

    # -----------------------------------
    # Standard round
    # --------------------------------------------------

    sock.send(
        f"ask(prgmlen({tour}))".encode()
    )

    response = sock.recv(
        1024
    ).decode()

    match = re.search(
    r"prgmlen\(\s*"
    + str(tour)
    + r"\s*,\s*(\w+|-?\d+)\s*\)",
    response,
    )

    if not match:
        return [], 0

    raw_value = match.group(1).strip().lower()

    # --------------------------------------------------
    # FINAL round
    # --------------------------------------------------

    if raw_value == "final":
        clauses = []
        clause_index = 0

        while True:
            sock.send(
                f"ask(prgm("
                f"{tour},"
                f"{clause_index}"
                f"))".encode()
            )

            response = sock.recv(
                4096
            ).decode()

            if (
                "failed" in response
                or "wait" in response
            ):
                break

            match_clause = re.search(
                r"\{\s*(.*?)\s*\}",
                response,
            )

            if not match_clause:
                break

            rule = match_clause.group(1).strip()

            if not rule.endswith("."):
                rule += "."

            clauses.append(rule)

            clause_index += 1

        return clauses, "final"

    # --------------------------------------------------
    # NORMAL round
    # --------------------------------------------------

    number_of_clauses = int(raw_value)

    
    clauses = []

    for clause_index in range(
        number_of_clauses
    ):

        sock.send(
            f"ask(prgm("
            f"{tour},"
            f"{clause_index}"
            f"))".encode()
        )

        response = sock.recv(
            4096
        ).decode()

        match = re.search(
            r"\{\s*(.*?)\s*\}",
            response,
        )

        if not match:
            continue

        rule = match.group(
            1
        ).strip()

        if not rule.endswith("."):
            rule += "."

        clauses.append(
            rule
        )

    return (
        clauses,
        number_of_clauses,
    )


# ======================================================
#  MAIN CLIENT LOOP
# ======================================================

def run_client():
    args = parse_arguments()

    client_id = int(args.client_id)

    dataset_path = resolve_dataset_path(
        args.dataset
    )

    store_address = parse_address(
        args.store_address
    )

    print(
        "========== BACH4POPPER CLIENT =========="
    )
    print(f"Client ID     : {client_id}")
    print(f"Dataset       : {dataset_path}")
    print(f"Store address : {args.store_address}")

    (
        settings,
        tester,
        stats,
    ) = initialisation(
        client_id=client_id,
        path_dir=dataset_path,
    )

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    sock.connect(
        store_address
    )

    try:
        tour = 0

        while True:
            (
                hypothesis,
                number_of_clauses,
            ) = popper_read_hypothesis(
                sock,
                tour,
            )

            # --------------------------------------------------
            # FINAL ROUND
            # --------------------------------------------------

            if number_of_clauses == "final":
                print(
                    "\nFINAL round detected"
                )

                print(
                    "Final hypothesis:"
                )

                for rule in hypothesis:
                    print(
                        " ",
                        rule,
                    )

                break

            # --------------------------------------------------
            # NORMAL ROUND
            # --------------------------------------------------

            print(
                f"\n========== ROUND {tour} =========="
            )

            print(
                "Received hypothesis:"
            )

            for rule in hypothesis:
                print(
                    " ",
                    rule,
                )

            # --------------------------------------------------
            # Local evaluation
            # --------------------------------------------------

            (
                epsilon_positive,
                epsilon_negative,
                score,
                inconsistent_rules,
                totally_incomplete_rules,
            ) = popper_test_hypothesis_final(
                hypothesis,
                tester,
                stats,
            )

            print(
                f"Local outcome = "
                f"({epsilon_positive}, "
                f"{epsilon_negative}), "
                f"score={score}"
            )

            # --------------------------------------------------
            # Send epsilon / score
            # --------------------------------------------------

            send_epair(
                sock=sock,
                client_id=client_id,
                tour=tour,
                epsilon_positive=epsilon_positive,
                epsilon_negative=epsilon_negative,
                score=score,
            )

            # --------------------------------------------------
            # Send clause-level feedback
            # --------------------------------------------------

            send_rule_feedback(
                sock=sock,
                client_id=client_id,
                tour=tour,
                inconsistent_rules=inconsistent_rules,
                totally_incomplete_rules=(
                    totally_incomplete_rules
                ),
            )

            tour += 1

    except Exception as error:
        print(
            "Client error:",
            error,
        )

        traceback.print_exc()

    finally:
        try:
            sock.send(
                b"close"
            )

            sock.settimeout(
                1.0
            )

            sock.recv(
                1024
            )

        except Exception:
            pass

        finally:
            sock.close()

        print(
            "Connection closed."
        )

        print(
            "\n========== CLIENT TIMING =========="
        )

        stats.show()


# ======================================================
#  ENTRY POINT
# ======================================================

if __name__ == "__main__":
    run_client()