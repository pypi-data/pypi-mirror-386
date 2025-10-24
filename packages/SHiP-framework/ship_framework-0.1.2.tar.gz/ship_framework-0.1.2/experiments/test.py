import numpy as np

from SHiP import SHiP
from SHiP.logger import LogLevel, setLogLevel
from SHiP.ultrametric_tree import UltrametricTreeType as UTreeType, AVAILABLE_ULTRAMETRIC_TREE_TYPES
from SHiP.partitioning import PartitioningMethod as PType, AVAILABLE_PARTITIONING_METHODS

from datasets.density_datasets import Datasets as DensityDatasets

import faulthandler
faulthandler.enable()

setLogLevel(LogLevel.INFO)



################################## SETUP ###################################
DATASETS = DensityDatasets.get_test_list()
RUNS = 2


excludeTreeTypes = [
    UTreeType.LoadTree,
]
TREE_TYPES = [treeType for treeType in AVAILABLE_ULTRAMETRIC_TREE_TYPES if treeType not in excludeTreeTypes]
HIERARCHIES = range(0, 5)
PARTITIONING_METHODS = AVAILABLE_PARTITIONING_METHODS


################################## SETUP END ###################################


for dataset in DATASETS:
    for run in range(RUNS):
        points, ground_truth = dataset.data_cached

        np.random.seed(0)
        seeds = np.random.choice(10_000, size=RUNS, replace=False)
        np.random.seed(seeds[run])
        shuffle_data_index = np.random.choice(len(points), size=len(points), replace=False)
        inverse_shuffle_data_index = np.empty_like(shuffle_data_index)
        inverse_shuffle_data_index[shuffle_data_index] = np.arange(len(points))
        points = points[shuffle_data_index]
        ground_truth = ground_truth[shuffle_data_index]

        k = len(np.unique(ground_truth))

        print("#" * 42)
        print(f"DATASET: {dataset.name}, RUN: {run}, n: {len(points)}, dim: {len(points[0])}, k: {k}")

        for treeType in TREE_TYPES:
            print(f"Start: {dataset.name}, {run}, {treeType}")
            config = {
                "k": k,
                "min_points": 5,
                "min_cluster_size": 15,
                "tiebreaker": "euclidean",
                "automatically_increase_too_small_costs": True,
            }
            ship = SHiP(data=points, treeType=treeType, config=config)

            for hierarchy in HIERARCHIES:
                for partitioningMethod in PARTITIONING_METHODS:
                    ship.hierarchy = hierarchy
                    ship.partitioningMethod = partitioningMethod

                    labels = ship.fit_predict(hierarchy, partitioningMethod)

                    # if treeType == UTreeType.DCTree and partitioningMethod in [PType.MedianOfElbows, PType.MeanOfElbows]:
                    #     print(f"hierarchy: {hierarchy}, partitioningMethod: {partitioningMethod}", end=" - ")
                    #     print(f"ARI: {round(ari(labels, ground_truth), 2):3.2f}")

                    if len(labels) != len(points):
                        exit(1)
