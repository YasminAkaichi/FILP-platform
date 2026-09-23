from core.benchmark import BenchmarkConfig
from core.benchmark_launcher import BenchmarkLauncher


config = BenchmarkConfig(
    name="zendo_k2_run_wall",
    approach="collaboration",
    dataset="zendo",
    number_of_clients=2,
    partition_strategy="iid",
    number_of_runs=6,
    base_seed=42,
    rounds=35000,
    timing_mode="cpu",
    server_address="localhost:8080",
)

launcher = BenchmarkLauncher()
benchmark_id = launcher.run(config)

print(f"Benchmark ID: {benchmark_id}")