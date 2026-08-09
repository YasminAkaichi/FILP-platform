from pathlib import Path

from partitioning.dataset_reader import read_dataset
from partitioning.partitioner import partition_dataset


dataset = read_dataset(
    Path("datasets/zendo1")
)

for strategy in ("iid", "non_iid"):
    print(f"\nStrategy: {strategy}")

    partitions = partition_dataset(
        dataset=dataset,
        number_of_clients=10,
        strategy=strategy,
        random_seed=42,
    )

    for partition in partitions:
        print(
            f"Client {partition.client_id}: "
            f"pos={len(partition.positive_examples)}, "
            f"neg={len(partition.negative_examples)}, "
            f"facts={len(partition.facts)}, "
            f"rules={len(partition.rules)}"
        )