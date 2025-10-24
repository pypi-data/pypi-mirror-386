import numpy as np
import os
import glob
import sys

from test_helpers import run_agglomerative,run_DPC,run_GaussianMixture,run_OPTICS, run_AMD_DBSCAN, run_LDClus, run_SCAR, run_HDBSCAN, run_Spectacl, run_kmeans

from SHiP import SHiP

from datasets.density_datasets import Datasets as DensityDatasets
from datasets.real_world_datasets import Datasets as RealWorldDatasets
from datasets.example_datasets import Datasets as ExampleDatasets

import faulthandler
faulthandler.enable()


# python -u main_save_labels.py 4 > >(tee logs/4.log) 2> >(tee logs/4.err >&2)

RUNS = 10

if sys.argv[1] == '1':
    savepath = "labels/density/"
    datasets = DensityDatasets

if sys.argv[1] == '2':
    savepath = "labels/real_world/"
    datasets = RealWorldDatasets.get_experiments_list()

if sys.argv[1] == '3':
    savepath = "labels/examples/"
    datasets = ExampleDatasets

if sys.argv[1] == '4':
    savepath = "labels/real_world/"
    datasets = [RealWorldDatasets.COIL100]

if sys.argv[1] == '5':
    savepath = "labels/real_world/"
    datasets = [RealWorldDatasets.MNIST]

if sys.argv[1] == '6':
    savepath = "labels/examples/"
    datasets = [ExampleDatasets.boxes3]


################################## SETUP ###################################
MIN_POINTS = 5
MIN_CLUSTER_SIZE = 15  # Default as cited here: https://hdbscan.readthedocs.io/en/latest/parameter_selection.html


# treeTypes = ["DCTree", "HST", "KDTree", "MeanSplitKDTree", "BallTree", "MeanSplitBallTree", "RPTree", "MaxRPTree", "UBTree", "VPTree", "RTree", "RStarTree", "RPlusTree", "RPlusPlusTree", "CoverTree"]
TREE_TYPES = ["DCTree", "HST", "KDTree", "CoverTree"]

HIERARCHIES = range(3)

PARTITIONING_METHODS = [
    "K",
    "Elbow",
    "Threshold",
    "ThresholdElbow",
    "QCoverage",
    "QCoverageElbow",
    "QStem",
    "QStemElbow",
    "LcaNoiseElbow",
    "LcaNoiseElbowNoTriangle",
    "MedianOfElbows",
    "MeanOfElbows",
    "Stability",
    "NormalizedStability",
]

extra_methods = False
extra_methods2 = False

competitors = False
comp1 = False
comp2 = False
competitors2 = False
competitors3 = False
competitors4 = False

################################## SETUP END ###################################


def run_and_cache(dataset, run, method_name, inverse_shuffle_data_index, func, args):
    savestring = f"{savepath}{dataset.name}##{method_name}##{run}"
    if len(glob.glob(savestring + ".npy")) > 0:
        print(f"Skipped: {dataset.name}, {run}, {method_name}")
    else:
        print(f"Start: {dataset.name}, {run}, {method_name}")
        labels, times = func(*args)
        os.makedirs(os.path.dirname(savestring), exist_ok=True)
        labels = labels[inverse_shuffle_data_index]
        time = times * 1000
        np.save(savestring + ".npy", labels)
        np.save(savestring + "##time.npy", time)


for dataset in datasets:
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

        # if False and len([path for hierarchy in PARTITIONING_METHODS for path in glob.glob(f"{savepath}{dataset.name}##{treeType}_{hierarchy}##{run}.npy")]) == len(PARTITIONING_METHODS):
        #     print(f"Skipped: {dataset.name}, {run}, {treeType}")

        for treeType in TREE_TYPES:
            print(f"Start: {dataset.name}, {run}, {treeType}")

            config = {"k": k, "min_points": MIN_POINTS, "min_cluster_size": MIN_CLUSTER_SIZE}
            ship = SHiP(points, treeType, config=config)

            np.save(f"{savepath}{dataset.name}##{treeType}_build##{run}" + "##time.npy", ship.tree_construction_runtime[0])

            for hierarchy in HIERARCHIES:
                for partitioningMethod in PARTITIONING_METHODS:
                    labels = ship.fit_predict(hierarchy=hierarchy, partitioningMethod=partitioningMethod)

                    savestring = f"{savepath}{dataset.name}##{treeType}_{hierarchy}_{partitioningMethod}##{run}"
                    os.makedirs(os.path.dirname(savestring), exist_ok=True)
                    labels = labels[inverse_shuffle_data_index]
                    np.save(savestring + ".npy", labels)
                    np.save(savestring + "##time.npy", ship.partitioning_runtime)


        # Competitors with ground truth 'k'
        if extra_methods:
            runtypes = ["euclidean_k_center", "euclidean_k_means", "agglomerative_single", "agglomerative_complete", "agglomerative_average", "agglomerative_median"]

            if len([path for runtype in runtypes for path in glob.glob(f"{savepath}{dataset.name}##{runtype}##{run}.npy")]) == len(runtypes):
                print(f"Skipped: {dataset.name}, {run}, extra_methods")

            else:
                print(f"Start: {dataset.name}, {run}, extra_methods")

                ## Refactored, use old saved runs

                for i, partitioningMethod in enumerate(runtypes):
                    savestring = f"{savepath}{dataset.name}##{partitioningMethod}##{run}"
                    os.makedirs(os.path.dirname(savestring), exist_ok=True)
                    labels = np.array(res[i])
                    labels = labels[inverse_shuffle_data_index]
                    runtype_time = times[i]
                    np.save(savestring + ".npy", labels)
                    np.save(savestring + "##time.npy", runtype_time)

        # Competitors with k = 500
        if extra_methods2:
            runtypes = ["euclidean_k_center", "euclidean_k_means", "agglomerative_single", "agglomerative_complete", "agglomerative_average", "agglomerative_median"]

            if len([path for runtype in runtypes for path in glob.glob(f"{savepath}{dataset.name}##{runtype}_500##{run}.npy")]) == len(runtypes):
                print(f"Skipped: {dataset.name}, {run}, extra_methods2")

            else:
                print(f"Start: {dataset.name}, {run}, extra_methods2")

                ## Refactored, use old saved runs

                for i, partitioningMethod in enumerate(runtypes):
                    savestring = f"{savepath}{dataset.name}##{partitioningMethod}_500##{run}"
                    os.makedirs(os.path.dirname(savestring), exist_ok=True)
                    labels = np.array(res[i])
                    labels = labels[inverse_shuffle_data_index]
                    runtype_time = times[i]
                    np.save(savestring + ".npy", labels)
                    np.save(savestring + "##time.npy", runtype_time)

        if competitors:
            run_and_cache(dataset, run, "HDBSCAN_python", inverse_shuffle_data_index, run_HDBSCAN, [points, k])
            run_and_cache(dataset, run, "agglomerative_ward_python", inverse_shuffle_data_index, run_agglomerative, [points, k])
            run_and_cache(dataset, run, "OPTICS_python", inverse_shuffle_data_index, run_OPTICS, [points, k])

        if comp1:
            if dataset.name != "COIL100":
                run_and_cache(dataset, run, "GaussianMixture_python", inverse_shuffle_data_index, run_GaussianMixture, [points, k])
        if comp2:
            run_and_cache(dataset, run, "DPC_python", inverse_shuffle_data_index, run_DPC, [points, k])

        if competitors2:
            run_and_cache(dataset, run, "AMD_DBSCAN_python", inverse_shuffle_data_index, run_AMD_DBSCAN, [points, k])
            run_and_cache(dataset, run, "Spectacl_python", inverse_shuffle_data_index, run_Spectacl, [points, k])
            run_and_cache(dataset, run, "SCAR_python", inverse_shuffle_data_index, run_SCAR, [points, k])

        if competitors3:
            run_and_cache(dataset, run, "LDClus_python", inverse_shuffle_data_index, run_LDClus, [points, k])

        if competitors4:
            run_and_cache(dataset, run, "k-means_python", inverse_shuffle_data_index, run_kmeans, [points, k])
            run_and_cache(dataset, run, "k-means_python_500", inverse_shuffle_data_index, run_kmeans, [points, min(500, len(points))])
