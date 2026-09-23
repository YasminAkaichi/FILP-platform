"""Flower server for Learning by Consensus.

How to run:

python -m engines.consensus.server \
  --num-clients 2 \
  --server-address 127.0.0.1:8080 \
  --output-dir artifacts/experiment_X/consensus
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import flwr as fl

from engines.consensus.strategy.consensus_strategy import (
    ConsensusStrategy,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Learning by Consensus Flower server"
    )

    parser.add_argument(
        "--num-clients",
        type=int,
        required=True,
        help="Number of Consensus clients",
    )

    parser.add_argument(
        "--server-address",
        default="0.0.0.0:8080",
    )

    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Directory where Consensus "
            "server results are written"
        ),
    )

    return parser.parse_args()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    args = parse_args()

    # --------------------------------------------------------
    # 1. Create Consensus strategy
    # --------------------------------------------------------

    strategy = ConsensusStrategy(
        num_clients=args.num_clients,
    )

    # --------------------------------------------------------
    # 2. Start Flower server
    # --------------------------------------------------------

    fl.server.start_server(
        server_address=args.server_address,
        config=fl.server.ServerConfig(
            num_rounds=1,
        ),
        strategy=strategy,
    )

    # --------------------------------------------------------
    # 3. Nothing to persist if no output directory is given
    # --------------------------------------------------------

    if args.output_dir is None:
        logging.info(
            "No output directory provided. "
            "Consensus results will not be persisted."
        )
        return

    output_dir = Path(
        args.output_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # 4. Main Consensus result
    # --------------------------------------------------------

    result = {
        "learner": (
            strategy.consensus_metrics.get(
                "learner"
            )
        ),
        "number_of_clients": args.num_clients,
        "number_of_hypotheses": len(
            strategy.hypotheses
        ),
        "hypotheses": [
            item["hypothesis"]
            for item in strategy.hypotheses
        ],
        "metrics": {
            key: value
            for key, value
            in strategy.consensus_metrics.items()
            if key != "learner"
        },
    }

    result_path = (
        output_dir
        / "server_result.json"
    )

    result_path.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    logging.info(
        "Consensus server result written to %s",
        result_path,
    )

    # --------------------------------------------------------
    # 5. Detailed prediction / voting traces
    # --------------------------------------------------------

    vote_traces_path = (
        output_dir
        / "vote_traces.json"
    )

    vote_traces_path.write_text(
        json.dumps(
            strategy.vote_traces,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    logging.info(
        "Consensus vote traces written to %s",
        vote_traces_path,
    )


if __name__ == "__main__":
    main()