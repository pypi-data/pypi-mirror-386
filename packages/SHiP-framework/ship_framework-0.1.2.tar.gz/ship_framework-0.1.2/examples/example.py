import numpy as np

from SHiP import SHiP
from SHiP.ultrametric_tree import UltrametricTreeType as UTreeType, AVAILABLE_ULTRAMETRIC_TREE_TYPES
from SHiP.partitioning import PartitioningMethod as PMethod, AVAILABLE_PARTITIONING_METHODS

from sklearn.metrics import adjusted_rand_score as ari
from sklearn.datasets import load_iris


# Load Example Dataset
data = load_iris()
X = data.data
gt_labels = data.target


# Decide for a UltrametricTreeType, Hierarchy, and PartitioningMethod
treeType = UTreeType.DCTree
hierarchy = 2
partitioningMethod = PMethod.Elbow

# Provide additional parameters (only used depending on the chosen partitioningMethod)
config = {
    "k": len(np.unique(gt_labels)),
    "min_points": 5,
    "min_cluster_size": 5,
    "tiebreaker_method": "euclidean_distance",
    "automatically_increase_too_small_costs": True,
}

# Build the tree by initializing an SHiP object
ship = SHiP(data=X, treeType=treeType, config=config)
# Extract the labels with the provided hierarchy and partitioningMethod
labels = ship.fit_predict(hierarchy, partitioningMethod)

print(
    f"ARI: {round(ari(gt_labels, labels), 2):3.2f}, #labels: {len(set(labels))}, tree_construction_runtime: {round(ship.tree_construction_runtime[0] / 1000)}ms, partitioning_runtime: {ship.partitioning_runtime}µs"
)

# Optional: Export the built tree in JSON format
json = ship.get_tree().to_json(fast_index=True)
