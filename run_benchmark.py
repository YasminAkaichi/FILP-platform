from core.benchmark import BenchmarkConfig
from core.benchmark_launcher import BenchmarkLauncher


config = BenchmarkConfig(
    name="zendo1_k2_run_10",
    approach="collaboration",
    dataset="trains2",
    number_of_clients=2,
    partition_strategy="iid",
    number_of_runs=1,
    base_seed=42,
    rounds=35000,
    server_address="localhost:8080",
)

launcher = BenchmarkLauncher()
benchmark_id = launcher.run(config)

print(f"Benchmark ID: {benchmark_id}")