from pathlib import Path

from partitioning.dataset_reader import read_dataset
from partitioning.partitioner import partition_dataset
from partitioning.writer import write_partitions


dataset = read_dataset(
    Path("datasets/zendo1")
)

partitions = partition_dataset(
    dataset=dataset,
    number_of_clients=10,
    strategy="non_iid",
    random_seed=42,
)

output_directory = write_partitions(
    dataset_name=dataset.name,
    partitions=partitions,
    strategy="non_iid",
    random_seed=42,
    output_root=Path("datasets/generated"),
)

print(f"Partitions written to: {output_directory}")