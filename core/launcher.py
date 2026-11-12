from __future__ import annotations
import json
import os
from core.results import ClientResult, ServerResult, ConsensusResult
import socket
import subprocess
import sys
import time
from pathlib import Path
from database.repository import ExperimentRepository
from core.experiment import ExperimentConfig
from partitioning.dataset_reader import read_dataset
from partitioning.partitioner import partition_dataset
from partitioning.writer import write_partitions
from partitioning.splitter import split_train_test
from partitioning.consensus_writer import write_consensus_dataset
from core.port_utils import find_free_port
from core.run_control import RunControl, RunStopped
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Popper's own evaluation time limit per example is 0.001 s: on a busy machine
# an example can exceed it by chance and be counted as "not covered", which
# makes the search take a different path from one run to the next. The
# federated approaches (Collaboration, Coordination) run several Prolog
# processes at once, so they use a safer limit. Override with the environment
# variable FILP_EVAL_TIMEOUT. PYTHONHASHSEED is fixed so that the order of
# Python sets and dictionaries (hence the order of the constraints given to
# the solver) is the same in every run.
FEDERATED_EVAL_TIMEOUT = "0.1"


def search_environment() -> dict:
    environment = os.environ.copy()
    environment["PYTHONHASHSEED"] = "0"
    environment.setdefault("FILP_EVAL_TIMEOUT", FEDERATED_EVAL_TIMEOUT)
    return environment
DATASETS_DIR = PROJECT_ROOT / "datasets"


class ExperimentLauncher:
    def run(
        self,
        config: ExperimentConfig,
        process_tracker: dict | None = None,
        control: RunControl | None = None,
    ) -> int:
        """
        control: optional RunControl (core/run_control.py). When the user
        presses "Stop" in the UI, the engines end their search as if their
        timeout had expired and the best result so far is saved. Raises
        RunStopped if the run was stopped before any result existed.


        process_tracker: an optional dict the caller keeps a reference to.
        As soon as this run's subprocesses (Flower/Bach server + clients)
        exist, their list is stored at process_tracker["processes"] — the
        SAME list object, so later appends (e.g. clients starting after
        the server) show up automatically without the caller polling
        again. Lets a UI running this in a background thread offer a
        "Cancel" button that can actually kill a stuck run.
        """
        config.validate()

        repository = ExperimentRepository()
        experiment_id = repository.create_experiment(config)

        print(f"[Launcher] Experiment ID: {experiment_id}")

        try:
            if config.approach == "collaboration":
                self._run_collaboration(
                    config=config,
                    experiment_id=experiment_id,
                    repository=repository,
                    process_tracker=process_tracker,
                    control=control,
                )

            elif config.approach == "consensus":
                self._run_consensus(
                    config=config,
                    experiment_id=experiment_id,
                    repository=repository,
                    control=control,
                )
            elif config.approach == "coordination":
                self._run_coordination(
                    config=config,
                    experiment_id=experiment_id,
                    repository=repository,
                    process_tracker=process_tracker,
                    control=control,
                )
            elif config.approach == "mdl_federation":
                self._run_mdl_federation(
                    config=config,
                    experiment_id=experiment_id,
                    repository=repository,
                    process_tracker=process_tracker,
                    control=control,
                )
            elif config.approach == "centralized":
                # Covers three single-learner, no-client, no-server
                # runs, selected via config.learner: "popper" (default),
                # "andante", and "mdl" — MaxSynth / noisy-MDL, "Learning
                # MDL Logic Programs From Noisy Data" (Hocquette,
                # Niskanen, Jarvisalo & Cropper, 2023).
                if config.reference_experiment_id is not None:
                    # "Run centralized on the same data" from the
                    # Experiments page: same split as a consensus run.
                    self._run_centralized_on_split(
                        config=config,
                        experiment_id=experiment_id,
                        repository=repository,
                        control=control,
                    )
                else:
                    self._run_centralized(
                        config=config,
                        experiment_id=experiment_id,
                        repository=repository,
                        control=control,
                    )
            else:
                raise NotImplementedError(
                    f"The approach '{config.approach}' is not implemented yet."
                )

            stopped_by_user = control is not None and control.stop_requested
            repository.complete_experiment(
                experiment_id,
                note=(
                    "Stopped by the user: best result found so far was kept."
                    if stopped_by_user
                    else None
                ),
            )

            print(
                f"[Launcher] Experiment {experiment_id} "
                "saved as COMPLETED."
            )
            return experiment_id

        except Exception as error:
            if control is not None and control.stop_requested:
                # The user pressed "Stop" and the engine could not return a
                # partial result (e.g. Andante, Consensus, or a forced kill):
                # this is a stop, not a failure.
                repository.stop_experiment(
                    experiment_id,
                    "Stopped by the user before a result was available "
                    f"({error}).",
                )
                print(
                    f"[Launcher] Experiment {experiment_id} "
                    "saved as STOPPED."
                )
                raise RunStopped(experiment_id) from error

            repository.fail_experiment(
                experiment_id=experiment_id,
                error_message=str(error),
            )

            print(
                f"[Launcher] Experiment {experiment_id} "
                "saved as FAILED."
            )

            raise

    def _run_collaboration(
    self,
    config: ExperimentConfig,
    experiment_id: int,
    repository: ExperimentRepository,
    process_tracker: dict | None = None,
    control: RunControl | None = None,
) -> None:
        server_dataset = DATASETS_DIR / config.dataset

        if not server_dataset.is_dir():
            raise FileNotFoundError(
                f"Server dataset not found: {server_dataset}"
            )

        #client_datasets = self._get_client_datasets(config)
        client_datasets = self._prepare_client_datasets(config)

        server_bind_address = self._get_server_bind_address(
            config.server_address
        )

        experiment_directory = (
            PROJECT_ROOT
            / "artifacts"
            / f"experiment_{experiment_id}"
        )

        experiment_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        if control is not None:
            control.register_directory(experiment_directory)

        print(
            f"[Launcher] Results directory: "
            f"{experiment_directory}"
        )

        # No --rounds here on purpose: it's no longer a real stopping
        # condition for collaboration (server.py defaults it to a huge
        # internal safety cap). The actual principle is "run until a
        # solution is found, or return the best hypothesis so far once
        # --timeout is reached" — see fedpopper.py's timeout_seconds.
        server_command = [
            sys.executable,
            "-m",
            "engines.collaboration.server",
            "--dataset",
            str(server_dataset),
            "--clients",
            str(config.number_of_clients),
            "--timeout",
            str(config.timeout),
            "--address",
            server_bind_address,
            "--output-dir",
            str(experiment_directory),
            "--timing-mode",
            config.timing_mode,
        ]

        print("\n========== STARTING EXPERIMENT ==========")
        print(f"Approach          : {config.approach}")
        print(f"Dataset           : {config.dataset}")
        print(f"Clients           : {config.number_of_clients}")
        print(f"Partition strategy: {config.partition_strategy}")
        print(f"Rounds            : {config.rounds}")
        print(f"Server address    : {config.server_address}")
        print("=========================================\n")

        processes: list[subprocess.Popen] = []
        client_processes: list[subprocess.Popen] = []

        if process_tracker is not None:
            # Same list object: appends below are visible to the caller
            # without it needing to poll this method again.
            process_tracker["processes"] = processes

        try:
            print("[Launcher] Starting server...")

            # The server's error output goes to a file so that, if it dies
            # during startup (e.g. a missing or incompatible dependency on a
            # deployment), the real cause is shown instead of a generic
            # message.
            server_log_path = experiment_directory / "server_stderr.log"
            server_log = open(server_log_path, "w")

            server_process = subprocess.Popen(
                server_command,
                cwd=PROJECT_ROOT,
                env=search_environment(),
                stderr=server_log,
            )

            processes.append(server_process)

            self._wait_for_server_ready(
                config.server_address,
                server_process,
            )

            if server_process.poll() is not None:
                server_log.flush()
                try:
                    tail = "\n".join(
                        server_log_path.read_text(errors="replace")
                        .strip()
                        .splitlines()[-12:]
                    )
                except OSError:
                    tail = ""
                raise RuntimeError(
                    "The Collaboration server stopped during startup."
                    + (f"\n\nServer error output:\n{tail}" if tail else "")
                )

            for client_id, client_dataset in enumerate(
                client_datasets,
                start=1,
            ):
                client_command = [
                    sys.executable,
                    "-m",
                    "engines.collaboration.client",
                    "--client-id",
                    str(client_id),
                    "--dataset",
                    str(client_dataset),
                    "--server-address",
                    config.server_address,
                    "--output-dir",
                    str(experiment_directory),
                ]

                print(
                    f"[Launcher] Starting client {client_id} "
                    f"with dataset {client_dataset.name}..."
                )

                client_process = subprocess.Popen(
                    client_command,
                    cwd=PROJECT_ROOT,
                    env=search_environment(),
                )

                processes.append(client_process)
                client_processes.append(client_process)

            server_return_code = self._wait_for(server_process, control)

            if server_return_code != 0:
                raise RuntimeError(
                    "The Collaboration server exited with code "
                    f"{server_return_code}."
                )
            # Wait for every client to disconnect and save its JSON result.
            for client_id, client_process in enumerate(
                client_processes,
                start=1,
            ):
                try:
                    client_return_code = client_process.wait(
                        timeout=30
                    )
                except subprocess.TimeoutExpired as error:
                    raise RuntimeError(
                        f"Client {client_id} did not stop within "
                        "30 seconds after the server finished."
                    ) from error

                if client_return_code != 0:
                    raise RuntimeError(
                        f"Client {client_id} exited with code "
                        f"{client_return_code}."
                    )

            server_result_path = (
                experiment_directory
                / "server_result.json"
            )

            if not server_result_path.is_file():
                raise FileNotFoundError(
                    f"Server result file not found: "
                    f"{server_result_path}"
                )

            server_data = json.loads(
                server_result_path.read_text(
                    encoding="utf-8"
                )
            )

            server_result = ServerResult(
                solution=server_data.get("solution"),
                solution_found=bool(
                    server_data.get(
                        "solution_found",
                        False,
                    )
                ),
                total_time=float(
                    server_data.get(
                        "total_time",
                        0.0,
                    )
                ),
                startup_time=float(
                    server_data.get(
                        "startup_time",
                        0.0,
                    )
                ),
                learning_time=float(
                    server_data.get(
                        "learning_time",
                        0.0,
                    )
                ),
                popper_time=float(
                    server_data.get(
                        "popper_time",
                        0.0,
                    )
                ),
                federation_time=float(
                    server_data.get(
                        "federation_time",
                        0.0,
                    )
                ),
                federation_ratio=float(
                    server_data.get(
                        "federation_ratio",
                        0.0,
                    )
                ),
                number_of_rounds=int(
                    server_data.get(
                        "number_of_rounds",
                        0,
                    )
                ),
                number_of_programs=int(
                    server_data.get(
                        "number_of_programs",
                        0,
                    )
                ),
                final_score=float(
                    server_data.get(
                        "final_score",
                        0.0,
                    )
                ),
                tp=int(
                    server_data.get(
                        "tp",
                        0,
                    )
                ),
                fn=int(
                    server_data.get(
                        "fn",
                        0,
                    )
                ),
                tn=int(
                    server_data.get(
                        "tn",
                        0,
                    )
                ),
                fp=int(
                    server_data.get(
                        "fp",
                        0,
                    )
                ),
            )

            client_results: list[ClientResult] = []

            for client_id in range(
                1,
                config.number_of_clients + 1,
            ):
                client_result_path = (
                    experiment_directory
                    / f"client_{client_id}_result.json"
                )

                if not client_result_path.is_file():
                    raise FileNotFoundError(
                        f"Client result file not found: "
                        f"{client_result_path}"
                    )

                client_data = json.loads(
                    client_result_path.read_text(
                        encoding="utf-8"
                    )
                )

                client_result = ClientResult(
                    client_id=int(
                        client_data["client_id"]
                    ),
                    dataset_partition=str(
                        client_data["dataset_partition"]
                    ),
                    number_of_examples=int(
                        client_data["number_of_examples"]
                    ),
                    number_of_positive_examples=int(
                        client_data[
                            "number_of_positive_examples"
                        ]
                    ),
                    number_of_negative_examples=int(
                        client_data[
                            "number_of_negative_examples"
                        ]
                    ),
                    number_of_evaluations=int(
                        client_data[
                            "number_of_evaluations"
                        ]
                    ),
                    total_eval_wall=float(
                        client_data[
                            "total_eval_wall"
                        ]
                    ),
                    total_eval_cpu=float(
                        client_data[
                            "total_eval_cpu"
                        ]
                    ),
                    average_eval_wall=float(
                        client_data[
                            "average_eval_wall"
                        ]
                    ),
                    average_eval_cpu=float(
                        client_data[
                            "average_eval_cpu"
                        ]
                    ),
                    total_evaluate_phase_wall=float(
                        client_data.get(
                            "total_evaluate_phase_wall", 0.0
                        )
                    ),
                    total_evaluate_phase_cpu=float(
                        client_data.get(
                            "total_evaluate_phase_cpu", 0.0
                        )
                    ),
                    final_epsilon_positive=str(
                        client_data[
                            "final_epsilon_positive"
                        ]
                    ),
                    final_epsilon_negative=str(
                        client_data[
                            "final_epsilon_negative"
                        ]
                    ),
                    accepted_solution=bool(
                        client_data[
                            "accepted_solution"
                        ]
                    ),
                    final_score=float(
                        client_data[
                            "final_score"
                        ]
                    ),
                    tp=int(
                        client_data["tp"]
                    ),
                    fn=int(
                        client_data["fn"]
                    ),
                    tn=int(
                        client_data["tn"]
                    ),
                    fp=int(
                        client_data["fp"]
                    ),
                )

                client_results.append(client_result)

            all_clients_accepted = all(
                result.accepted_solution
                for result in client_results
            )

            repository.save_server_result(
                experiment_id=experiment_id,
                result=server_result,
                all_clients_accepted=all_clients_accepted,
            )

            for client_result in client_results:
                repository.save_client_result(
                    experiment_id=experiment_id,
                    result=client_result,
                )

            hypothesis_log_path = (
                experiment_directory
                / "hypothesis_log.json"
            )

            if hypothesis_log_path.is_file():
                hypothesis_log_entries = json.loads(
                    hypothesis_log_path.read_text(
                        encoding="utf-8"
                    )
                )

                repository.save_hypothesis_log(
                    experiment_id=experiment_id,
                    entries=hypothesis_log_entries,
                )

            print(
                "\n[Launcher] Experiment completed successfully."
            )

        except KeyboardInterrupt:
            print(
                "\n[Launcher] Experiment interrupted by the user."
            )

            raise

        finally:
            self._stop_processes(processes)

    
    def _run_consensus(
    self,
    config: ExperimentConfig,
    experiment_id: int,
    repository: ExperimentRepository,
    control: RunControl | None = None,
) -> None:
        source_dataset_directory = (
            DATASETS_DIR / config.dataset
        )

        if not source_dataset_directory.is_dir():
            raise FileNotFoundError(
                f"Source dataset not found: "
                f"{source_dataset_directory}"
            )

        print(
            "\n[Launcher] Preparing Consensus experiment..."
        )

        # --------------------------------------------------
        # 1. Read the complete original dataset
        # --------------------------------------------------

        dataset = read_dataset(
            source_dataset_directory
        )

        # --------------------------------------------------
        # 2. Global TRAIN / TEST split
        # --------------------------------------------------

        test_ratio = 0.2

        train_dataset, test_dataset = split_train_test(
            dataset=dataset,
            test_ratio=test_ratio,
            random_seed=config.random_seed,
        )

        print(
            "[Launcher] Global split: "
            f"train={len(train_dataset.positive_examples) + len(train_dataset.negative_examples)} "
            f"examples, "
            f"test={len(test_dataset.positive_examples) + len(test_dataset.negative_examples)} "
            f"examples"
        )

        # --------------------------------------------------
        # 3. Partition TRAIN only between clients
        # --------------------------------------------------

        train_partitions = partition_dataset(
            dataset=train_dataset,
            number_of_clients=config.number_of_clients,
            strategy=config.partition_strategy,
            random_seed=config.random_seed,
        )

        # --------------------------------------------------
        # 4. Write client TRAIN datasets + common TEST
        # --------------------------------------------------

        consensus_directory = write_consensus_dataset(
            dataset_name=config.dataset,
            train_partitions=train_partitions,
            test_dataset=test_dataset,
            strategy=config.partition_strategy,
            random_seed=config.random_seed,
            test_ratio=test_ratio,
            output_root=DATASETS_DIR / "generated",
        )

        client_datasets = [
            consensus_directory
            / "train"
            / f"{config.dataset}_part{client_id}"
            for client_id in range(
                1,
                config.number_of_clients + 1
            )
        ]

        global_test_dataset = (
            consensus_directory / "test"
        )

        print(
            "[Launcher] Consensus datasets ready:"
        )

        for client_id, client_dataset in enumerate(
            client_datasets,
            start=1,
        ):
            print(
                f"  Client {client_id}: "
                f"{client_dataset}"
            )

        print(
            f"  Global test: {global_test_dataset}"
        )

        # --------------------------------------------------
        # 5. Prepare Consensus result directory
        # --------------------------------------------------

        consensus_output_directory = (
            PROJECT_ROOT
            / "artifacts"
            / f"experiment_{experiment_id}"
            / "consensus"
        )

        consensus_output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        if control is not None:
            control.register_directory(consensus_output_directory)

        # Andante reads ONE native .pl file per dataset, whereas the
        # partitioner writes Popper directories (bias/bk/exs). The same
        # partitions are converted, so both learners see the same data.
        consensus_test_dataset = global_test_dataset
        consensus_client_datasets = list(client_datasets)

        if config.learner == "andante":
            from partitioning.popper_to_andante import (
                convert_popper_to_andante,
            )

            def _to_andante_file(directory):
                directory = Path(directory)
                if directory.is_file():
                    return directory
                return convert_popper_to_andante(
                    directory,
                    directory.parent / f"{directory.name}.andante.pl",
                )

            consensus_test_dataset = _to_andante_file(
                global_test_dataset
            )
            consensus_client_datasets = [
                _to_andante_file(directory)
                for directory in client_datasets
            ]


        server_bind_address = self._get_server_bind_address(
            config.server_address
        )

        server_command = [
            sys.executable,
            "-m",
            "engines.consensus.server",
            "--num-clients",
            str(config.number_of_clients),
            "--server-address",
            server_bind_address,
            "--output-dir",
            str(consensus_output_directory),
        ]

        print(
            "\n[Launcher] Starting Consensus server..."
        )

        processes = []
        client_processes = []

        try:
            server_process = subprocess.Popen(
                server_command,
                cwd=PROJECT_ROOT,
            )

            processes.append(server_process)

            time.sleep(2)

            if server_process.poll() is not None:
                raise RuntimeError(
                    "Consensus server stopped unexpectedly "
                    "during startup."
                )

            # --------------------------------------------------
            # 6. Start Consensus clients
            # --------------------------------------------------

            for client_id, client_dataset in enumerate(
                consensus_client_datasets,
                start=1,
            ):
                client_command = [
                    sys.executable,
                    "-m",
                    "engines.consensus.client",
                    "--client-id",
                    str(client_id),
                    "--learner",
                    config.learner,
                    "--dataset",
                    str(client_dataset),
                    "--test-dataset",
                    str(consensus_test_dataset),
                    "--server-address",
                    config.server_address,
                    "--timeout",
                    str(config.timeout),
                ]

                print(
                    f"[Launcher] Starting Consensus "
                    f"client {client_id}..."
                )

                client_process = subprocess.Popen(
                    client_command,
                    cwd=PROJECT_ROOT,
                )

                processes.append(client_process)
                client_processes.append(client_process)

            # --------------------------------------------------
            # 7. Wait for Flower
            # --------------------------------------------------

            # The Consensus learners cannot return a partial result, so after a
            # "Stop" the processes are ended after a short grace period.
            server_return_code = self._wait_for(
                server_process,
                control,
                grace_seconds=5.0,
            )

            if server_return_code != 0:
                raise RuntimeError(
                    "Consensus server failed with return code "
                    f"{server_return_code}."
                )

            for client_id, client_process in enumerate(
                client_processes,
                start=1,
            ):
                client_return_code = client_process.wait(
                    timeout=30
                )

                if client_return_code != 0:
                    raise RuntimeError(
                        f"Consensus client {client_id} failed "
                        f"with return code "
                        f"{client_return_code}."
                    )

            print(
                "\n[Launcher] Consensus Flower execution "
                "completed successfully."
            )
            # --------------------------------------------------
            # 7. Load and persist Consensus result
            # --------------------------------------------------

            server_result_path = (
                consensus_output_directory
                / "server_result.json"
            )

            if not server_result_path.is_file():
                raise FileNotFoundError(
                    f"Consensus server result not found: "
                    f"{server_result_path}"
                )

            with server_result_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                raw_result = json.load(file)

            metrics = raw_result["metrics"]

            consensus_result = ConsensusResult(
                learner=raw_result["learner"],
                number_of_clients=raw_result["number_of_clients"],
                number_of_hypotheses=raw_result[
                    "number_of_hypotheses"
                ],
                hypotheses=raw_result["hypotheses"],
                tp=metrics["tp"],
                fn=metrics["fn"],
                tn=metrics["tn"],
                fp=metrics["fp"],
                accuracy=metrics["accuracy"],
                precision=metrics["precision"],
                recall=metrics["recall"],
                f1=metrics["f1"],
            )

            repository.save_consensus_result(
                experiment_id=experiment_id,
                result=consensus_result,
            )

            print(
                "[Launcher] Consensus result saved "
                "to database."
            )

            # --------------------------------------------------
            # 8. Persist each client's local dataset partition,
            #    so the Dataset explorer tab has something to show.
            # --------------------------------------------------

            for client_id, (client_dataset, partition) in enumerate(
                zip(client_datasets, train_partitions),
                start=1,
            ):
                repository.save_client_dataset_info(
                    experiment_id=experiment_id,
                    client_id=client_id,
                    dataset_partition=str(client_dataset),
                    number_of_examples=(
                        len(partition.positive_examples)
                        + len(partition.negative_examples)
                    ),
                    number_of_positive_examples=len(
                        partition.positive_examples
                    ),
                    number_of_negative_examples=len(
                        partition.negative_examples
                    ),
                )

            print(
                "[Launcher] Client dataset partitions saved "
                "to database."
            )

        except KeyboardInterrupt:
            print(
                "\n[Launcher] Consensus experiment "
                "interrupted by the user."
            )
            raise

        finally:
            self._stop_processes(processes)




    def _run_coordination(
    self,
    config: ExperimentConfig,
    experiment_id: int,
    repository: ExperimentRepository,
    process_tracker: dict | None = None,
    control: RunControl | None = None,) -> None:

        server_dataset = (
            DATASETS_DIR
            / config.dataset
        )

        if not server_dataset.is_dir():
            raise FileNotFoundError(
                f"Server dataset not found: {server_dataset}"
            )

        # Same partitioning pipeline as Collaboration
        client_datasets = (
            self._prepare_client_datasets(
                config
            )
        )

        experiment_directory = (
            PROJECT_ROOT
            / "artifacts"
            / f"experiment_{experiment_id}"
        )

        experiment_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        if control is not None:
            control.register_directory(experiment_directory)

        print(
            "\n========== STARTING COORDINATION EXPERIMENT =========="
        )

        print(
            f"Approach          : {config.approach}"
        )
        print(
            f"Dataset           : {config.dataset}"
        )
        print(
            f"Clients           : {config.number_of_clients}"
        )
        print(
            f"Partition strategy: {config.partition_strategy}"
        )
        print(
            f"Rounds            : {config.rounds}"
        )

        print(
            "======================================================\n"
        )

        processes: list[subprocess.Popen] = []
        client_processes: list[subprocess.Popen] = []

        if process_tracker is not None:
            process_tracker["processes"] = processes

        # --------------------------------------------------
        # Bach store
        # --------------------------------------------------

        bach_directory = (
            PROJECT_ROOT
            / "coordination"
            / "bach"
        )

        bbpopper_path = (
            bach_directory
            / "bbpopper.py"
        )

        if not bbpopper_path.is_file():
            raise FileNotFoundError(
                f"Bach store launcher not found: "
                f"{bbpopper_path}"
            )

        try:

            # --------------------------------------------------
            # 1. Start Bach store
            # --------------------------------------------------

            print(
                "[Launcher] Starting Bach coordination store..."
            )

            # A fresh port per run instead of the historical hardcoded
            # 8000, so two Coordination experiments running at the same
            # time (different users, or two tabs) each get their own
            # Bach store instead of the second one failing to bind.
            store_port = find_free_port()
            store_address = f"127.0.0.1:{store_port}"

            store_process = subprocess.Popen(
                [
                    sys.executable,
                    "bbpopper.py",
                    "--port",
                    str(store_port),
                ],
                cwd=bach_directory,
            )

            processes.append(
                store_process
            )

            time.sleep(1)

            if store_process.poll() is not None:
                raise RuntimeError(
                    "The Bach coordination store "
                    "stopped during startup."
                )

            # --------------------------------------------------
            # 2. Start Coordination server
            # --------------------------------------------------

            print(
                "[Launcher] Starting Bach4Popper server..."
            )

            server_command = [
                sys.executable,
                "-m",
                "engines.coordination.srvpopper",

                "--dataset",
                str(server_dataset),

                "--clients",
                str(config.number_of_clients),

                "--rounds",
                str(config.rounds),

                "--timeout",
                str(config.timeout),

                "--store-address",
                store_address,

                "--timing-mode",
                config.timing_mode,

                "--output-dir",
                str(experiment_directory),
            ]

            server_process = subprocess.Popen(
                server_command,
                cwd=PROJECT_ROOT,
                env=search_environment(),
            )

            processes.append(
                server_process
            )

            time.sleep(1)

            if server_process.poll() is not None:
                raise RuntimeError(
                    "The Coordination server "
                    "stopped during startup."
                )

            # --------------------------------------------------
            # 3. Start clients
            # --------------------------------------------------

            for client_id, client_dataset in enumerate(
                client_datasets,
                start=1,
            ):

                client_command = [
                    sys.executable,
                    "-m",
                    "engines.coordination.clipopper",

                    "--client-id",
                    str(client_id),

                    "--dataset",
                    str(client_dataset),

                    "--store-address",
                    store_address,

                    "--output-dir",
                    str(experiment_directory),
                ]

                print(
                    f"[Launcher] Starting Coordination client "
                    f"{client_id} with dataset "
                    f"{client_dataset.name}..."
                )

                client_process = subprocess.Popen(
                    client_command,
                    cwd=PROJECT_ROOT,
                    env=search_environment(),
                )

                processes.append(
                    client_process
                )

                client_processes.append(
                    client_process
                )

            # --------------------------------------------------
            # 4. Wait for server
            # --------------------------------------------------

            server_return_code = self._wait_for(
                server_process,
                control,
            )

            if server_return_code != 0:
                raise RuntimeError(
                    "The Coordination server exited "
                    f"with code {server_return_code}."
                )

            print(
                "[Launcher] Coordination server completed."
            )

            # --------------------------------------------------
            # 5. Clients
            #
            # We already know some Bach clients can remain
            # waiting after the final hypothesis.
            # Do NOT fail the whole experiment for that.
            # --------------------------------------------------

            for client_id, client_process in enumerate(
                client_processes,
                start=1,
            ):

                try:
                    client_process.wait(
                        timeout=3
                    )

                except subprocess.TimeoutExpired:

                    print(
                        f"[Launcher] Client {client_id} "
                        "is still waiting after server completion. "
                        "Stopping it cleanly."
                    )

                    client_process.terminate()

                    try:
                        client_process.wait(
                            timeout=2
                        )

                    except subprocess.TimeoutExpired:
                        client_process.kill()
                        client_process.wait()

            print(
                "\n[Launcher] Coordination experiment "
                "completed successfully."
            )

            # --------------------------------------------------
            # Read back server_result.json and every
            # client_<id>_result.json, and persist them — mirrors the
            # Collaboration path above. srvpopper.py doesn't compute
            # tp/fn/tn/fp for the server-side aggregate, so those are
            # stored as 0 rather than guessed (see the comment in
            # srvpopper.py where server_result.json is written); each
            # client's own tp/fn/tn/fp (from its local confusion
            # matrix) is real, not a placeholder.
            # --------------------------------------------------

            server_result_path = (
                experiment_directory
                / "server_result.json"
            )

            if not server_result_path.is_file():
                raise FileNotFoundError(
                    f"Server result file not found: "
                    f"{server_result_path}"
                )

            server_data = json.loads(
                server_result_path.read_text(
                    encoding="utf-8"
                )
            )

            server_result = ServerResult(
                solution=server_data.get("solution"),
                solution_found=bool(
                    server_data.get("solution_found", False)
                ),
                total_time=float(server_data.get("total_time", 0.0)),
                startup_time=float(server_data.get("startup_time", 0.0)),
                learning_time=float(server_data.get("learning_time", 0.0)),
                popper_time=float(server_data.get("popper_time", 0.0)),
                federation_time=float(
                    server_data.get("federation_time", 0.0)
                ),
                federation_ratio=float(
                    server_data.get("federation_ratio", 0.0)
                ),
                number_of_rounds=int(
                    server_data.get("number_of_rounds", 0)
                ),
                number_of_programs=int(
                    server_data.get("number_of_programs", 0)
                ),
                final_score=float(server_data.get("final_score", 0.0)),
                tp=int(server_data.get("tp", 0)),
                fn=int(server_data.get("fn", 0)),
                tn=int(server_data.get("tn", 0)),
                fp=int(server_data.get("fp", 0)),
            )

            coordination_client_results: list[ClientResult] = []

            for client_id in range(
                1,
                config.number_of_clients + 1,
            ):
                client_result_path = (
                    experiment_directory
                    / f"client_{client_id}_result.json"
                )

                if not client_result_path.is_file():
                    # Bach clients can be waiting on the store after the
                    # final hypothesis and get force-terminated by
                    # _stop_processes (see the comment above, at step 5)
                    # — clipopper.py now saves its result on SIGTERM
                    # too, but a client that doesn't exit within the
                    # grace period there still gets SIGKILL'd, which
                    # can't be caught. Skip it rather than failing the
                    # whole experiment, exactly like a hanging client
                    # process itself doesn't fail the experiment.
                    print(
                        f"[Launcher] Warning: no result file for "
                        f"coordination client {client_id} "
                        f"({client_result_path}) — it was likely "
                        "terminated before it could save. Skipping "
                        "this client's result."
                    )
                    continue

                client_data = json.loads(
                    client_result_path.read_text(
                        encoding="utf-8"
                    )
                )

                coordination_client_results.append(
                    ClientResult(
                        client_id=int(client_data["client_id"]),
                        dataset_partition=str(
                            client_data["dataset_partition"]
                        ),
                        number_of_examples=int(
                            client_data["number_of_examples"]
                        ),
                        number_of_positive_examples=int(
                            client_data["number_of_positive_examples"]
                        ),
                        number_of_negative_examples=int(
                            client_data["number_of_negative_examples"]
                        ),
                        number_of_evaluations=int(
                            client_data["number_of_evaluations"]
                        ),
                        total_eval_wall=float(
                            client_data["total_eval_wall"]
                        ),
                        total_eval_cpu=float(
                            client_data["total_eval_cpu"]
                        ),
                        average_eval_wall=float(
                            client_data["average_eval_wall"]
                        ),
                        average_eval_cpu=float(
                            client_data["average_eval_cpu"]
                        ),
                        final_epsilon_positive=str(
                            client_data["final_epsilon_positive"]
                        ),
                        final_epsilon_negative=str(
                            client_data["final_epsilon_negative"]
                        ),
                        accepted_solution=bool(
                            client_data["accepted_solution"]
                        ),
                        final_score=float(client_data["final_score"]),
                        tp=int(client_data["tp"]),
                        fn=int(client_data["fn"]),
                        tn=int(client_data["tn"]),
                        fp=int(client_data["fp"]),
                    )
                )

            # all(...) on an empty list is vacuously True — guard against
            # claiming "all accepted" when every client's result was
            # actually skipped above.
            all_clients_accepted = bool(coordination_client_results) and all(
                result.accepted_solution
                for result in coordination_client_results
            )

            repository.save_server_result(
                experiment_id=experiment_id,
                result=server_result,
                all_clients_accepted=all_clients_accepted,
            )

            for client_result in coordination_client_results:
                repository.save_client_result(
                    experiment_id=experiment_id,
                    result=client_result,
                )

            # Every program tested, in order, with its outcome and score:
            # lets two searches be compared round by round.
            coordination_log_path = (
                experiment_directory / "hypothesis_log.json"
            )

            if coordination_log_path.is_file():
                repository.save_hypothesis_log(
                    experiment_id=experiment_id,
                    entries=json.loads(
                        coordination_log_path.read_text(encoding="utf-8")
                    ),
                )

        except KeyboardInterrupt:

            print(
                "\n[Launcher] Coordination experiment "
                "interrupted by the user."
            )

            raise

        finally:

            self._stop_processes(
                processes
            )

    def _run_mdl_federation(
        self,
        config: ExperimentConfig,
        experiment_id: int,
        repository: ExperimentRepository,
        process_tracker: dict | None = None,
        control: RunControl | None = None,
    ) -> None:
        """
        FedMDL: federated MaxSynth / noisy-MDL. Same client/server process
        shape as _run_collaboration (one Flower server, N clients, each on
        its own partition) — see engines/mdl_federation/strategy/fedmdl.py
        for how the search/combine protocol itself differs from FedPopper.

        NOTE: FedMDL clients never see the final combined program during
        the run. For the dashboard, once the run is over the launcher
        evaluates that program on each client's own partition (a separate
        local process, nothing goes back to the server) to fill the
        per-client confusion matrix and per-clause coverage.
        """

        server_dataset = DATASETS_DIR / config.dataset

        if not server_dataset.is_dir():
            raise FileNotFoundError(
                f"Server dataset not found: {server_dataset}"
            )

        client_datasets = self._prepare_client_datasets(config)

        server_bind_address = self._get_server_bind_address(
            config.server_address
        )

        experiment_directory = (
            PROJECT_ROOT
            / "artifacts"
            / f"experiment_{experiment_id}"
        )
        experiment_directory.mkdir(parents=True, exist_ok=True)

        if control is not None:
            control.register_directory(experiment_directory)

        server_command = [
            sys.executable,
            "-m",
            "engines.mdl_federation.server",
            "--dataset",
            str(server_dataset),
            "--clients",
            str(config.number_of_clients),
            "--timeout",
            str(config.timeout),
            "--address",
            server_bind_address,
            "--output-dir",
            str(experiment_directory),
            "--timing-mode",
            config.timing_mode,
        ]

        print("\n========== STARTING FEDMDL EXPERIMENT ==========")
        print(f"Approach          : {config.approach}")
        print(f"Dataset           : {config.dataset}")
        print(f"Clients           : {config.number_of_clients}")
        print(f"Partition strategy: {config.partition_strategy}")
        print(f"Server address    : {config.server_address}")
        print("==================================================\n")

        processes: list[subprocess.Popen] = []
        client_processes: list[subprocess.Popen] = []

        if process_tracker is not None:
            process_tracker["processes"] = processes

        try:
            print("[Launcher] Starting FedMDL server...")

            server_process = subprocess.Popen(
                server_command,
                cwd=PROJECT_ROOT,
            )
            processes.append(server_process)

            self._wait_for_server_ready(
                config.server_address,
                server_process,
            )

            if server_process.poll() is not None:
                raise RuntimeError(
                    "The FedMDL server stopped during startup."
                )

            for client_id, client_dataset in enumerate(client_datasets, start=1):
                client_command = [
                    sys.executable,
                    "-m",
                    "engines.mdl_federation.client",
                    "--client-id",
                    str(client_id),
                    "--dataset",
                    str(client_dataset),
                    "--server-address",
                    config.server_address,
                    "--output-dir",
                    str(experiment_directory),
                ]

                print(
                    f"[Launcher] Starting FedMDL client {client_id} "
                    f"with dataset {client_dataset.name}..."
                )

                client_process = subprocess.Popen(
                    client_command,
                    cwd=PROJECT_ROOT,
                )
                processes.append(client_process)
                client_processes.append(client_process)

            server_return_code = self._wait_for(server_process, control)

            if server_return_code != 0:
                raise RuntimeError(
                    "The FedMDL server exited with code "
                    f"{server_return_code}."
                )

            for client_id, client_process in enumerate(client_processes, start=1):
                try:
                    client_process.wait(timeout=30)
                except subprocess.TimeoutExpired as error:
                    raise RuntimeError(
                        f"FedMDL client {client_id} did not stop within "
                        "30 seconds after the server finished."
                    ) from error

            server_result_path = experiment_directory / "server_result.json"

            if not server_result_path.is_file():
                raise FileNotFoundError(
                    f"Server result file not found: {server_result_path}"
                )

            server_data = json.loads(
                server_result_path.read_text(encoding="utf-8")
            )

            server_result = ServerResult(
                solution=server_data.get("solution"),
                solution_found=bool(server_data.get("solution_found", False)),
                total_time=float(server_data.get("total_time", 0.0)),
                startup_time=float(server_data.get("startup_time", 0.0)),
                learning_time=float(server_data.get("learning_time", 0.0)),
                popper_time=float(server_data.get("popper_time", 0.0)),
                federation_time=float(server_data.get("federation_time", 0.0)),
                federation_ratio=float(server_data.get("federation_ratio", 0.0)),
                number_of_rounds=int(server_data.get("number_of_rounds", 0)),
                number_of_programs=int(server_data.get("number_of_programs", 0)),
                final_score=float(server_data.get("final_score", 0.0)),
                tp=int(server_data.get("tp", 0)),
                fn=int(server_data.get("fn", 0)),
                tn=int(server_data.get("tn", 0)),
                fp=int(server_data.get("fp", 0)),
            )

            repository.save_server_result(
                experiment_id=experiment_id,
                result=server_result,
                all_clients_accepted=server_result.solution_found,
            )

            # Per-client rows: each client's own activity (client_N_result.json)
            # plus the final program evaluated on its local partition
            # (simulation-side, see engines/mdl_federation/evaluate_final.py).
            solution_rules = [
                line.strip()
                for line in (server_result.solution or "").splitlines()
                if ":-" in line
            ]
            solution_file = experiment_directory / "final_program.pl"
            solution_file.write_text("\n".join(solution_rules), encoding="utf-8")

            for client_id, client_dataset in enumerate(client_datasets, start=1):
                client_json = experiment_directory / f"client_{client_id}_result.json"
                client_data = (
                    json.loads(client_json.read_text(encoding="utf-8"))
                    if client_json.is_file()
                    else {}
                )

                evaluation: dict = {}
                if solution_rules:
                    evaluation_path = experiment_directory / f"client_{client_id}_final_eval.json"
                    completed = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "engines.mdl_federation.evaluate_final",
                            "--dataset",
                            str(client_dataset),
                            "--solution-file",
                            str(solution_file),
                            "--output",
                            str(evaluation_path),
                        ],
                        cwd=PROJECT_ROOT,
                    )
                    if completed.returncode == 0 and evaluation_path.is_file():
                        evaluation = json.loads(
                            evaluation_path.read_text(encoding="utf-8")
                        )
                    else:
                        print(
                            f"[Launcher] Warning: could not evaluate the final "
                            f"program on client {client_id}'s partition."
                        )

                num_pos = int(
                    evaluation.get("num_pos", client_data.get("number_of_positive_examples", 0))
                )
                num_neg = int(
                    evaluation.get("num_neg", client_data.get("number_of_negative_examples", 0))
                )
                tp = int(evaluation.get("tp", 0))
                tn = int(evaluation.get("tn", 0))

                repository.save_client_result(
                    experiment_id=experiment_id,
                    result=ClientResult(
                        client_id=client_id,
                        dataset_partition=str(client_dataset),
                        number_of_examples=num_pos + num_neg,
                        number_of_positive_examples=num_pos,
                        number_of_negative_examples=num_neg,
                        number_of_evaluations=int(client_data.get("number_of_evaluations", 0)),
                        total_eval_wall=float(client_data.get("total_eval_wall", 0.0)),
                        total_eval_cpu=0.0,
                        average_eval_wall=float(client_data.get("average_eval_wall", 0.0)),
                        average_eval_cpu=0.0,
                        final_epsilon_positive="n/a",
                        final_epsilon_negative="n/a",
                        accepted_solution=bool(evaluation),
                        final_score=float(tp + tn),
                        tp=tp,
                        fn=int(evaluation.get("fn", 0)),
                        tn=tn,
                        fp=int(evaluation.get("fp", 0)),
                        clause_coverage=(
                            json.dumps(evaluation["clauses"])
                            if evaluation.get("clauses")
                            else None
                        ),
                    ),
                )

            hypothesis_log_path = experiment_directory / "hypothesis_log.json"

            if hypothesis_log_path.is_file():
                hypothesis_log_entries = json.loads(
                    hypothesis_log_path.read_text(encoding="utf-8")
                )
                repository.save_hypothesis_log(
                    experiment_id=experiment_id,
                    entries=hypothesis_log_entries,
                )

            print("\n[Launcher] FedMDL experiment completed successfully.")

        except KeyboardInterrupt:
            print("\n[Launcher] FedMDL experiment interrupted by the user.")
            raise

        finally:
            self._stop_processes(processes)

    def _run_centralized(
        self,
        config: ExperimentConfig,
        experiment_id: int,
        repository: ExperimentRepository,
        control: RunControl | None = None,
    ) -> None:
        """
        A non-federated baseline: run a single ILP learner once on the
        whole dataset — no clients, no server, no network. This is what
        the "Learning" tab on the Inductive Logic Programming page triggers.

        Four learners are supported via config.learner (the
        "noisy_mdl" approach forces learner="mdl" from the wizard):
          - "popper" (default): Popper 1.1.0 (popper-core)
          - "popper-v4": Popper 4 (symbolic/popper-v4), the version used by
            Learning by Consensus
          - "andante": Andante, a Progol-style ILP system already used
            by Learning by Consensus
          - "mdl": MaxSynth / noisy-MDL (symbolic/Popper-v3), the
            generate-test-combine-constrain engine from "Learning MDL
            Logic Programs From Noisy Data" (arXiv:2308.09393)

        All three run as a SUBPROCESS, not in-process. For Popper and
        MaxSynth, this is required: both use signal.alarm() for their
        internal timeout, which only works in a process's main thread,
        and Streamlit executes each page in a worker thread — calling
        learn_solution() directly from a Streamlit callback fails with
        "signal only works in main thread of the main interpreter".
        Andante has no such constraint, but is run the same way for
        consistency and so a pathological run can still be killed on
        timeout without risking the Streamlit process itself.
        """

        learner = config.learner or "popper"
        if learner == "andante":
            runner_module = "engines.centralized.andante_runner"
        elif learner == "mdl":
            runner_module = "engines.centralized.mdl_runner"
        elif learner == "popper-v4":
            runner_module = "engines.centralized.popper4_runner"
        else:
            runner_module = "engines.centralized.runner"

        learner_label = {
            "andante": "Andante",
            "mdl": "MaxSynth / noisy MDL, Popper-v3",
            "popper-v4": "Popper 4, popper-v4",
        }.get(learner, "Popper 1.1.0, popper-core")

        if learner == "andante":
            # Native Andante examples are single .pl files under
            # datasets/andante/ (e.g. family.pl, short_family.pl) —
            # hand-written, not derived from a Popper dataset directory.
            dataset_path = DATASETS_DIR / "andante" / f"{config.dataset}.pl"
            if not dataset_path.is_file():
                raise FileNotFoundError(
                    f"Andante dataset not found: {dataset_path}"
                )
        else:
            # Both "popper" and "mdl" consume the same bias.pl/bk.pl/exs.pl
            # dataset directory format.
            dataset_path = DATASETS_DIR / config.dataset
            if not dataset_path.is_dir():
                raise FileNotFoundError(
                    f"Dataset not found: {dataset_path}"
                )

        experiment_directory = (
            PROJECT_ROOT
            / "artifacts"
            / f"experiment_{experiment_id}"
        )

        experiment_directory.mkdir(parents=True, exist_ok=True)

        if control is not None:
            control.register_directory(experiment_directory)

        print("\n========== STARTING CENTRALIZED RUN ==========")
        print(f"Approach : centralized ({learner_label})")
        print(f"Dataset  : {config.dataset}")
        print(f"Timeout  : {config.timeout}s")
        print("================================================\n")

        runner_command = [
            sys.executable,
            "-m",
            runner_module,
            "--dataset",
            str(dataset_path),
            "--timeout",
            str(config.timeout),
            "--output-dir",
            str(experiment_directory),
        ]

        process = subprocess.Popen(
            runner_command,
            cwd=PROJECT_ROOT,
            env=search_environment(),
        )

        try:
            return_code = self._wait_for(
                process,
                control,
                hard_timeout=config.timeout + 30,
                # Popper and MaxSynth return their best program at once
                # (they handle the stop like a timeout); Andante cannot
                # return a partial result, so it is ended quickly.
                grace_seconds=3.0 if learner == "andante" else 30.0,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(
                f"The centralized {learner_label} run exceeded its timeout."
            ) from error

        if return_code != 0:
            raise RuntimeError(
                f"The centralized {learner_label} run exited with code "
                f"{return_code}."
            )

        result_path = experiment_directory / "server_result.json"

        if not result_path.is_file():
            raise FileNotFoundError(
                f"Centralized run result not found: {result_path}"
            )

        server_data = json.loads(result_path.read_text(encoding="utf-8"))

        server_result = ServerResult(
            solution=server_data.get("solution"),
            solution_found=bool(server_data.get("solution_found", False)),
            total_time=float(server_data.get("total_time", 0.0)),
            startup_time=float(server_data.get("startup_time", 0.0)),
            learning_time=float(server_data.get("learning_time", 0.0)),
            popper_time=float(server_data.get("popper_time", 0.0)),
            federation_time=float(server_data.get("federation_time", 0.0)),
            federation_ratio=float(server_data.get("federation_ratio", 0.0)),
            number_of_rounds=int(server_data.get("number_of_rounds", 0)),
            number_of_programs=int(server_data.get("number_of_programs", 0)),
            final_score=float(server_data.get("final_score", 0.0)),
            tp=int(server_data.get("tp", 0)),
            fn=int(server_data.get("fn", 0)),
            tn=int(server_data.get("tn", 0)),
            fp=int(server_data.get("fp", 0)),
        )

        repository.save_server_result(
            experiment_id=experiment_id,
            result=server_result,
            all_clients_accepted=server_result.solution_found,
        )

        print(
            "\n[Launcher] Centralized run completed "
            f"({'solution found' if server_result.solution_found else 'no solution'} "
            f"in {server_result.total_time:.2f}s, "
            f"{server_result.number_of_programs} programs tested)."
        )

    def _run_centralized_on_split(
        self,
        config: ExperimentConfig,
        experiment_id: int,
        repository: ExperimentRepository,
        control: RunControl | None = None,
    ) -> None:
        """Centralized baseline of a consensus run.

        Same dataset, same seed, hence the same train/test split as the
        consensus experiment (the split only depends on the dataset and the
        seed). The learner (Popper-v4 or Andante) runs ONCE on the whole
        training set, no clients and no Flower, and its hypothesis is scored
        on the common test set.
        """
        source_directory = DATASETS_DIR / config.dataset
        if not source_directory.is_dir():
            raise FileNotFoundError(f"Source dataset not found: {source_directory}")

        test_ratio = 0.2
        dataset = read_dataset(source_directory)
        train_dataset, test_dataset = split_train_test(
            dataset=dataset,
            test_ratio=test_ratio,
            random_seed=config.random_seed,
        )
        # One partition holding the whole training set.
        partitions = partition_dataset(
            dataset=train_dataset,
            number_of_clients=1,
            strategy="iid",
            random_seed=config.random_seed,
        )
        split_directory = write_consensus_dataset(
            dataset_name=config.dataset,
            train_partitions=partitions,
            test_dataset=test_dataset,
            strategy="iid",
            random_seed=config.random_seed,
            test_ratio=test_ratio,
            output_root=DATASETS_DIR / "generated",
        )
        train_path = split_directory / "train" / f"{config.dataset}_part1"
        test_path = split_directory / "test"

        if config.learner == "andante":
            from partitioning.popper_to_andante import convert_popper_to_andante

            train_path = convert_popper_to_andante(
                train_path, train_path.parent / f"{train_path.name}.andante.pl"
            )
            test_path = convert_popper_to_andante(
                test_path, test_path.parent / f"{test_path.name}.andante.pl"
            )

        output_directory = (
            PROJECT_ROOT / "artifacts" / f"experiment_{experiment_id}" / "consensus"
        )
        output_directory.mkdir(parents=True, exist_ok=True)
        if control is not None:
            control.register_directory(output_directory)

        print("\n========== CENTRALIZED RUN ON THE CONSENSUS SPLIT ==========")
        print(f"Consensus experiment : #{config.reference_experiment_id}")
        print(f"Learner / dataset    : {config.learner} / {config.dataset}")
        print(f"Seed                 : {config.random_seed}")
        print("=============================================================\n")

        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "engines.consensus.centralized_baseline",
                "--learner", config.learner,
                "--dataset", str(train_path),
                "--test-dataset", str(test_path),
                "--output-dir", str(output_directory),
                "--timeout", str(config.timeout),
            ],
            cwd=PROJECT_ROOT,
        )
        return_code = self._wait_for(
            process,
            control,
            hard_timeout=config.timeout + 60,
            grace_seconds=3.0,
        )
        if return_code != 0:
            raise RuntimeError(
                f"The centralized {config.learner} run exited with code {return_code}."
            )

        result = json.loads(
            (output_directory / "server_result.json").read_text(encoding="utf-8")
        )
        analysis = json.loads(
            (output_directory / "consensus_analysis.json").read_text(encoding="utf-8")
        )
        metrics = result["metrics"]
        hypothesis = result["hypotheses"][0] if result["hypotheses"] else []
        learning_time = float(
            (analysis.get("induction_time_per_client") or {}).get("1", 0.0)
        )

        server_result = ServerResult(
            solution="\n".join(hypothesis) if hypothesis else None,
            solution_found=bool(hypothesis),
            total_time=float(analysis.get("federated_round_seconds", learning_time)),
            startup_time=0.0,
            learning_time=learning_time,
            popper_time=learning_time,
            federation_time=0.0,
            federation_ratio=0.0,
            number_of_rounds=1,
            number_of_programs=0,
            final_score=float(metrics["accuracy"]),
            tp=int(metrics["tp"]),
            fn=int(metrics["fn"]),
            tn=int(metrics["tn"]),
            fp=int(metrics["fp"]),
        )
        repository.save_server_result(
            experiment_id=experiment_id,
            result=server_result,
            all_clients_accepted=server_result.solution_found,
        )
        print(
            "\n[Launcher] Centralized baseline saved "
            f"(accuracy {metrics['accuracy']:.3f} on the common test set)."
        )

    def _get_client_datasets_old(
        self,
        config: ExperimentConfig,
    ) -> list[Path]:
        client_datasets = []

        for client_id in range(1, config.number_of_clients + 1):
            client_dataset = (
                DATASETS_DIR
                / f"{config.dataset}_part{client_id}"
            )

            if not client_dataset.is_dir():
                raise FileNotFoundError(
                    f"Dataset partition for client {client_id} "
                    f"not found: {client_dataset}"
                )

            client_datasets.append(client_dataset)

        return client_datasets
    

 

    def _prepare_client_datasets(
    self,
    config: ExperimentConfig,
) -> list[Path]:
        source_dataset_directory = (
            DATASETS_DIR / config.dataset
        )

        if not source_dataset_directory.is_dir():
            raise FileNotFoundError(
                f"Source dataset not found: "
                f"{source_dataset_directory}"
            )

        partition_directory = (
            DATASETS_DIR
            / "generated"
            / config.dataset
            / (
                f"{config.partition_strategy}_"
                f"{config.number_of_clients}_"
                f"seed_{config.random_seed}"
            )
        )

        expected_client_directories = [
            partition_directory
            / f"{config.dataset}_part{client_id}"
            for client_id in range(
                1,
                config.number_of_clients + 1,
            )
        ]

        partitions_already_exist = (
            partition_directory.is_dir()
            and all(
                client_directory.is_dir()
                for client_directory
                in expected_client_directories
            )
        )

        if partitions_already_exist:
            print(
                "[Launcher] Reusing existing partitions: "
                f"{partition_directory}"
            )

            return expected_client_directories

        print(
            "[Launcher] Generating partitions: "
            f"dataset={config.dataset}, "
            f"strategy={config.partition_strategy}, "
            f"clients={config.number_of_clients}, "
            f"seed={config.random_seed}"
        )

        dataset = read_dataset(
            source_dataset_directory
        )

        partitions = partition_dataset(
            dataset=dataset,
            number_of_clients=config.number_of_clients,
            strategy=config.partition_strategy,
            random_seed=config.random_seed,
        )

        generated_directory = write_partitions(
            dataset_name=dataset.name,
            partitions=partitions,
            strategy=config.partition_strategy,
            random_seed=config.random_seed,
            output_root=DATASETS_DIR / "generated",
        )

        client_directories = [
            generated_directory
            / f"{config.dataset}_part{client_id}"
            for client_id in range(
                1,
                config.number_of_clients + 1,
            )
        ]

        for client_directory in client_directories:
            if not client_directory.is_dir():
                raise FileNotFoundError(
                    "Generated client partition not found: "
                    f"{client_directory}"
                )

        print(
            f"[Launcher] Partitions generated in: "
            f"{generated_directory}"
        )

        return client_directories


    def _wait_for(
        self,
        process: subprocess.Popen,
        control: RunControl | None = None,
        grace_seconds: float = 90.0,
        hard_timeout: float | None = None,
    ) -> int:
        """
        process.wait() that also reacts to the "Stop" button.

        When the user stops the run, the engines notice the STOP file and
        finish by themselves (best result so far saved, normal exit code).
        If the process is still alive grace_seconds after the request —
        Andante and the Consensus learners cannot return a partial result,
        or a final combine takes very long — it is terminated.
        hard_timeout (seconds) kills the process and raises
        subprocess.TimeoutExpired.
        """
        started = time.monotonic()
        stop_seen_at: float | None = None

        while True:
            try:
                return process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                pass

            now = time.monotonic()

            if hard_timeout is not None and now - started > hard_timeout:
                process.kill()
                process.wait()
                raise subprocess.TimeoutExpired(process.args, hard_timeout)

            if control is not None and control.stop_requested:
                if stop_seen_at is None:
                    stop_seen_at = now
                    print(
                        "[Launcher] Stop requested: waiting for the engine "
                        "to return its best result so far..."
                    )
                elif now - stop_seen_at > grace_seconds:
                    print(
                        "[Launcher] The engine did not stop by itself: "
                        "terminating it."
                    )
                    process.terminate()
                    try:
                        return process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        return process.wait()

    @staticmethod
    def _wait_for_server_ready(
        address: str,
        server_process: subprocess.Popen,
        timeout: float = 30.0,
        poll_interval: float = 0.1,
    ) -> None:
        """Actively probe the server's port instead of sleeping a fixed
        amount of time before launching clients.

        A fixed sleep that's occasionally too short (system load, a
        slower import, etc.) lets a client's first connection attempt
        race ahead of the server actually listening. Flower's own gRPC
        client then falls into its exponential-backoff retry loop
        (1s, 2s, 4s, 8s, 16s, capped at MAX_RETRY_DELAY=20s — see
        flwr.supercore.retry) before it finally connects, which can
        inflate a run's measured "startup_time" from ~2s to over a
        minute even though the server was, in fact, ready within a
        couple of seconds. Actively waiting for the port to accept a
        connection removes the race instead of just widening it.
        """
        host, port_str = address.rsplit(":", maxsplit=1)
        port = int(port_str)
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            if server_process.poll() is not None:
                # Let the caller's own poll() check raise its usual
                # "stopped during startup" error with its own message.
                return

            try:
                with socket.create_connection(
                    (host, port),
                    timeout=poll_interval,
                ):
                    return
            except OSError:
                time.sleep(poll_interval)

        raise RuntimeError(
            f"Timed out after {timeout:.0f}s waiting for the "
            f"Collaboration server to start listening on {address}."
        )

    @staticmethod
    def _get_server_bind_address(
        client_server_address: str,
    ) -> str:
        """
        Convert localhost:8080, used by clients, into 0.0.0.0:8080,
        used by the Flower server.
        """
        if ":" not in client_server_address:
            raise ValueError(
                "The server address must use the format host:port."
            )

        _, port = client_server_address.rsplit(":", maxsplit=1)

        if not port.isdigit():
            raise ValueError(
                f"Invalid server port: {port}"
            )

        return f"0.0.0.0:{port}"

    @staticmethod
    def _stop_processes(
        processes: list[subprocess.Popen],
    ) -> None:
        for process in processes:
            if process.poll() is None:
                process.terminate()

        for process in processes:
            if process.poll() is not None:
                continue

            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()



"""
launch consensus: 
PYTHONPATH="$PWD/symbolic/popper-v4:$PWD" \
python -c "
from core.launcher import ExperimentLauncher
from core.experiment import ExperimentConfig

config = ExperimentConfig(
    approach='consensus',
    dataset='zendo1',
    number_of_clients=2,
    partition_strategy='iid',
    learner='popper',
    random_seed=42,
)

launcher = ExperimentLauncher()

launcher._run_consensus(
    config=config,
    experiment_id=999,
    repository=None,
)
"

"""