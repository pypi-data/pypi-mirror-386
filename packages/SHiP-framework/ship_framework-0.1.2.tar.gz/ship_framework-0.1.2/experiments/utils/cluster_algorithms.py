import os
import sys

parent_folder = os.path.dirname(os.path.abspath("./"))
sys.path.append(parent_folder)


import numpy as np
from sklearn.cluster import KMeans, DBSCAN, HDBSCAN, SpectralClustering, MeanShift, AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score as ARI, normalized_mutual_info_score as NMI
# from src.Evaluation.dcdistances.dctree import DCTree
from SHiP import SHiP
from clusterer.kcenter import kcenter
from clusterer.DPC import DensityPeakCluster

from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from kneed import KneeLocator



def optimal_k_dbscan(X, l):
    dctree = DCTree(X, min_points=5, min_points_mr=3)

    l_ = np.full(len(l), -1)
    best_ari = 0

    for k in range(2, 4 * len(set(l))):
        eps = dctree.get_eps_for_k(k)
        l_dbscan = DBSCAN(eps).fit(X).labels_
        l_kcenter = dctree.get_k_center(k)
        ari = ARI(l_dbscan, l_kcenter)
        if best_ari - 0.01 <= ari:
            l_ = l_dbscan
            best_ari = ari
    return l_


# Not sure how to select `eps`. Tried to do elbow method for eps.
# DBSCAN for a given ground truth "k" would probably be kcenter q-coverage
def run_DBSCAN(X, min_pts = 5):
    nbrs = NearestNeighbors(n_neighbors=min_pts).fit(X)
    distances, _indices = nbrs.kneighbors(X)
    distance_desc = np.sort(distances[:,-1])[::-1]

    kneedle = KneeLocator(
        range(1,len(distance_desc)+1),  # imdex values
        distance_desc,  # eps values
        S=1.0,
        curve="convex",
        direction="decreasing",
    )

    dbscan = DBSCAN(eps=kneedle.knee_y)
    dbscan.fit(X)
    return dbscan.labels_

def run_SHiP(X, treeType, hierarchy, partitioningMethod, config = {}):
    ship = SHiP(X, treeType, hierarchy, partitioningMethod, config)
    return ship.fit_predict()

# \emph{ground truth} clustering, \emph{$k$-center} over Euclidean metric, \emph{$k$-means} over Euclidean metric, \emph{$kd$-tree/$k$-center/$k$}, \emph{$kd$-tree/$k$-means/$k$}, \emph{$kd$-tree/$k$-means/$k$*} with $k$ chosen by elbow-method, \emph{$kd$-tree/$k$-means/norm.stability} 

CLUSTER_ALGORITHMS_KDTREE = {
    # "ground truth": lambda X, l: l,
    # "OptimalKDBSCAN": lambda X, l: optimal_k_dbscan(X, l),
    # "DBSCAN": lambda X, l: DBSCAN(DCTree(X).get_eps_for_k(len(set(l)))).fit(X).labels_,
    "$k$-center": lambda X, l: kcenter(X, len(set(l))),
    "$k$-means": lambda X, l: KMeans(len(set(l))).fit(X).labels_,
    "$k$-d tree/$k$-center/$k$": lambda X, l: run_SHiP(X, "KDTree", 0, "K", {"k": len(set(l))}),
    "$k$-d tree/$k$-means/$k$": lambda X, l: run_SHiP(X, "KDTree", 2, "K", {"k": len(set(l))}), 
    "$k$-d tree/$k$-means/$k$*": lambda X, l: run_SHiP(X, "KDTree", 2, "Elbow"),
    "$k$-d tree/$k$-means/norm.stability": lambda X, l: run_SHiP(X, "KDTree", 0, "NormalizedStability"),
}

CLUSTER_ALGORITHMS_DCTREE = {
    "ground truth": lambda X, l: l,
    "DBSCAN": lambda X, l: run_DBSCAN(X),
    "HDBSCAN": lambda X, l: HDBSCAN().fit(X).labels_,
    "$dc$-tree/$k$-means/$k$": lambda X, l: run_SHiP(X, "DCTree", 2, "K", {"k": len(set(l))}), 
    "$dc$-tree/$k$-means/$k$*": lambda X, l: run_SHiP(X, "DCTree", 2, "Elbow"), 
    "$dc$-tree/$k$-means/norm.stability": lambda X, l: run_SHiP(X, "DCTree", 2, "NormalizedStability"),
}


# CLUSTER_ALGORITHMS_DCTREE_FULL = {
#     "ground truth": lambda X, l: l,
#     "DBSCAN": lambda X, l: run_DBSCAN(X),
#     "HDBSCAN": lambda X, l: HDBSCAN().fit(X).labels_,
#     "DPC": lambda X, l: DensityPeakCluster().fit(X).labels_,
#     "SpectralClustering": lambda X, l: SpectralClustering(len(set(l))).fit(X).labels_,
#     "Agglomerative": lambda X, l: AgglomerativeClustering(len(set(l))).fit(X).labels_,
#     "MeanShift": lambda X, l: MeanShift().fit(X).labels_,
# }


# SELECTED_CLUSTER_ALGORITHMS = CLUSTER_ALGORITHMS.keys()

CLUSTER_ABBREV = {
    "GroundTruth": "GT",
    "OptimalKDBSCAN": "K'-DBSCAN",
    "DBSCAN": "DBSCAN",
    "KCenter": "KCenter",
    "HDBSCAN": "HDBSCAN",
    "DPC": "DPC",
    "SpectralClustering": "SC",
    "Agglomerative": "Aggl.",
    "MeanShift": "MeanShift",
    "KMeans": "KMeans",
}
