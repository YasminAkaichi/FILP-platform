from __future__ import annotations
import json
from core.results import ClientResult, ServerResult
import subprocess
import sys
import time
from pathlib import Path
from database.repository import ExperimentRepository
from core.experiment import ExperimentConfig
from partitioning.dataset_reader import read_dataset
from partitioning.partitioner import partition_dataset
from partitioning.writer import write_partitions

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASETS_DIR = PROJECT_ROOT / "datasets"


class ExperimentLauncher:
    def run(self, config: ExperimentConfig) -> int:
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
                )
            else:
                raise NotImplementedError(
                    f"The approach '{config.approach}' is not implemented yet."
                )

            repository.complete_experiment(experiment_id)
            

            print(
                f"[Launcher] Experiment {experiment_id} "
                "saved as COMPLETED."
            )
            return experiment_id

        except Exception as error:
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

        print(
            f"[Launcher] Results directory: "
            f"{experiment_directory}"
        )

        server_command = [
            sys.executable,
            "-m",
            "engines.collaboration.server",
            "--dataset",
            str(server_dataset),
            "--clients",
            str(config.number_of_clients),
            "--rounds",
            str(config.rounds),
            "--address",
            server_bind_address,
            "--output-dir",
            str(experiment_directory),
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

        try:
            print("[Launcher] Starting server...")

            server_process = subprocess.Popen(
                server_command,
                cwd=PROJECT_ROOT,
            )

            processes.append(server_process)

            time.sleep(2)

            if server_process.poll() is not None:
                raise RuntimeError(
                    "The Collaboration server stopped during startup."
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
                )

                processes.append(client_process)
                client_processes.append(client_process)

            server_return_code = server_process.wait()

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