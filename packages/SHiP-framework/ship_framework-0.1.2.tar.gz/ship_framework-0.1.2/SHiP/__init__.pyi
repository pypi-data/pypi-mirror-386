from . import logger as logger, partitioning as partitioning, ultrametric_tree as ultrametric_tree
from typing import List, Optional, Dict
import numpy as np

class SHiP:
    treeType: ultrametric_tree.UltrametricTreeType  # read-only
    hierarchy: int
    partitioningMethod: partitioning.PartitioningMethod | str
    config: dict

    labels_: list[int]  # read-only

    partitioning_runtime: int  # read-only
    tree_construction_runtime: dict[int, int]  # read-only

    def __init__(
        self,
        data: list[list[float]] | np.ndarray,
        treeType: ultrametric_tree.UltrametricTreeType | str = ...,
        hierarchy: int = ...,
        partitioningMethod: partitioning.PartitioningMethod | str = ...,
        config: dict = ...,
    ) -> None: ...
    def fit(
        self,
        hierarchy: int = ...,
        partitioningMethod: partitioning.PartitioningMethod | str = ...,
    ) -> None: ...
    def fit_predict(
        self,
        hierarchy: int = ...,
        partitioningMethod: partitioning.PartitioningMethod | str = ...,
    ) -> list[int]: ...
    def get_tree(self, hierarchy: int = 0) -> Tree: ...

class Node:
    id: int
    cost: float
    children: List["Node"]
    parent: Optional["Node"]
    size: int
    low: int
    high: int
    level: int

    def __lt__(self, other: "Node") -> bool: ...
    def __gt__(self, other: "Node") -> bool: ...
    def to_json(self, fast_index: bool = False) -> str: ...

class Tree:
    root: Node
    tree_type: ultrametric_tree.UltrametricTreeType
    hierarchy: int
    config: Dict[str, str]
    index_order: List[int]
    sorted_nodes: List[Node]
    costs: List[float]

    def get_elbow_k(self, triangle: bool = True) -> int: ...
    def distance_matrix(self) -> np.ndarray: ...
    def to_json(self, fast_index: bool = False) -> str: ...
