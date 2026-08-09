from pathlib import Path

from partitioning.dataset_reader import read_dataset


dataset = read_dataset(
    Path("datasets/zendo1")
)

print("Name:", dataset.name)
print("Positive examples:", len(dataset.positive_examples))
print("Negative examples:", len(dataset.negative_examples))
print("Facts:", len(dataset.facts))
print("Rules:", len(dataset.rules))

print("\nFirst positive example:")
print(dataset.positive_examples[0])

print("\nFirst fact:")
print(dataset.facts[0])