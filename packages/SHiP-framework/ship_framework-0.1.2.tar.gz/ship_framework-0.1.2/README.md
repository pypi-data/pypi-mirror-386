# Similarity-Hierarchical-Partitioning (SHiP) Clustering Framework
[![PyPI version](https://badge.fury.io/py/SHiP-framework.svg)](https://pypi.org/project/SHiP-framework/)
[![Tests](https://github.com/pasiweber/SHiP-framework/actions/workflows/publish_to_pypi.yml/badge.svg)](https://github.com/pasiweber/SHiP-framework/actions/workflows/publish_to_pypi.yml)
[![Docs](https://readthedocs.org/projects/SHiP-framework/badge/?version=latest)](https://SHiP-framework.readthedocs.io/en/)

This repository is the official implementation of the Similarity-Hierarchical-Partitioning (SHiP) clustering framework proposed in [Ultrametric Cluster Hierarchies: I Want `em All!](https://github.com/pasiweber/SHiP-framework/) This framework provides a comprehensive approach to clustering by leveraging similarity trees, $(k,z)$-hierarchies, and various partitioning objective functions. 

The whole project is implemented in C++ and Python bindings enable the usage within Python.


## Overview
The SHiP framework operates in three main stages:
[![SHiP framework overview](https://raw.githubusercontent.com/pasiweber/SHiP-framework/main/docs/ClusterFrameworkOverview.png)](https://github.com/pasiweber/SHiP-framework/)

1. **Similarity Tree Construction:** A similarity tree is built for the given dataset. This tree represents the relationships and proximities between data points. Note that the default constructed tree corresponds to the $k$-center hierarchy (Section 3 in the paper).
2. **$(k,z)$-Hierarchy Construction:** Using the similarity tree, a $(k,z)$-hierarchy can be constructed. These hierarchies correlate to common center based clustering methods, as e.g., $k$-median or $k$-means (Section 4).
3. **Partitioning:** Finally, the data is partitioned based on the constructed hierarchy and a user-selected partitioning objective function (Section 5).


## Features
- **Similarity Trees:** The package provides a set of similarity/ultrametric tree implementations:
  - `DCTree` [[1]](#references)
  - `HST` [[2]](#references)
  - `CoverTree` [[3]](#references)
  - `KDTree` [[3]](#references)
  - `MeanSplitKDTree` [[3]](#references)
  - `BallTree` [[3]](#references)
  - `MeanSplitBallTree` [[3]](#references)
  - `RPTree` [[3]](#references)
  - `MaxRPTree` [[3]](#references)
  - `UBTree` [[3]](#references)
  - `RTree` [[3]](#references)
  - `RStarTree` [[3]](#references)
  - `XTree` [[3]](#references)
  - `HilbertRTree` [[3]](#references)
  - `RPlusTree` [[3]](#references)
  - `RPlusPlusTree` [[3]](#references)
  - Or use `LoadTree` to load a precomputed tree


- **$(k,z)$-Hierarchies:** It supports all possible $(k,z)$-hierarchies, allowing flexibility in choosing the most suitable hierarchy for a given dataset.
  - $z = 0$ &rarr; $k$-center (actually in theory: $z = ∞$, but in this implementation we use 0 for $∞$)
  - $z = 1$ &rarr; $k$-median
  - $z = 2$ &rarr; $k$-means
  - ...

- **Partitioning Functions:** A wide range of partitioning functions are available, enabling users to select the most appropriate function based on their specific needs:
  - `K`
  - `Elbow`
  - `Threshold`
  - `ThresholdElbow`
  - `QCoverage`
  - `QCoverageElbow`
  - `QStem`
  - `QStemElbow`
  - `LcaNoiseElbow`
  - `LcaNoiseElbowNoTriangle`
  - `MedianOfElbows`
  - `MeanOfElbows`
  - `Stability`
  - `NormalizedStability`

- **Customization:** Users can customize the framework by selecting from the available similarity trees, $(k,z)$-
hierarchies, and partitioning functions.
  - E.g., `DCTree` with $k$-means ($z=2$)-hierarchy and the `Elbow` partitioning method.
    ```python
    from SHiP import SHiP

    # Build the `DCTree`
    ship = SHiP(data=data_points, treeType="DCTree")
    # Extract the clustering from the $k$-median hierarchy and the `Elbow` partitioning method
    labels = ship.fit_predict(hierarchy=2, partitioningMethod="Elbow")
    ```


## Installation
### Stable Version
The current stable version can be installed by the following command:<br/>
`pip install SHiP-framework` (coming soon)

Note that a gcc compiler is required for installation.
Therefore, in case of an installation error, make sure that:
- Windows: [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/de/visual-cpp-build-tools/) is installed
- Linux/Mac: Python dev is installed (e.g., by running `apt-get install python-dev` - the exact command may differ depending on the linux distribution)

The error messages may look like this:
```
error: command 'gcc' failed: No such file or directory
Could not build wheels for SHiP-framework, which is required to install pyproject.toml-based projects
Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools
```


### Development Version
The current development version can be installed directly from git by executing:<br/>
`sudo pip install git+https://github.com/pasiweber/SHiP-framework.git`

Alternatively, clone the repository, go to the root directory and execute:<br/>
`pip install .`


## Code Example
```python
from SHiP import SHiP

ship = SHiP(data=data, treeType="DCTree")

# or to load a saved tree
ship = SHiP(data=data, treeType="LoadTree", config={"json_tree_filepath": "<file_path>"}) 
# or additionally specify the tree_type of the loaded tree by adding {"tree_type": "DCTree"}

ship.hierarchy = 0
ship.partitioningMethod = "K"
labels = ship.fit_predict()

# or in one line
labels = ship.fit_predict(hierarchy = 1, partitioningMethod = "Elbow")

# optional: save the current computed tree
json = ship.get_tree().to_json()
```


## Results
Our framework achieves the following performance:

Dataset | DC-0-Stab. | DC-1-MoE | DC-2-Elb. | CT-0-Stab. | CT-1-MoE | CT-2-Elb. | $k$-means | SCAR | Ward | AMD-DBSCAN | DPC |
|-|-|-|-|-|-|-|-|-|-|-|-|
| Boxes | 90.1 | **99.3** | _97.9_ | 2.6 | 42.1 ± 4.7 | 24.2 ± 1.6 | 93.5 ± 4.3 | 0.1 ± 0.1 | 95.8 | 63.9 | 25.9 |
| D31 | 79.7 | 42.7 | 82.9 | 46.5 ± 1.8 | 62.0 ± 5.4 | 67.7 ± 3.2 | **92.0 ± 2.7** | 41.7 ± 5.4 | **92.0** | _86.4_ | 18.5 |
| airway | 38.0 | **65.9** | 58.8 | 0.8 | 18.2 ± 2.4 | 12.0 ± 1.4 | 39.9 ± 2.0 | -0.9 ± 0.5 | 43.7 | 31.7 | _65.1_ |
| lactate | 41.0 | 41.0 | _67.5_ | 0.1 | 4.1 ± 0.6 | 1.7 ± 0.2 | 28.6 ± 1.1 | 1.5 ± 1.0 | 27.7 | **71.5** | 0.0 |
| HAR | 30.0 | 46.9 | **52.8** | 14.7 ± 8.8 | 14.2 ± 4.7 | 9.6 ± 2.2 | 46.0 ± 4.5 | 5.5 ± 3.2 | _49.1_ | 0.0 | 33.2 |
| letterrec. | 12.1 | _16.6_ | **17.9** | 5.8 ± 0.2 | 7.2 ± 0.6 | 6.2 ± 0.3 | 12.9 ± 0.6 | 0.4 ± 0.1 | 14.7 ± 0.9 | 7.9 | 0.0 |
| PenDigits | 66.4 | _73.1_ | **75.4** | 8.0 ± 0.8 | 12.0 ± 0.6 | 8.9 ± 0.5 | 55.3 ± 3.2 | 0.9 ± 0.3 | 55.2 | 55.6 | 28.8 ± 1.1 |
| COIL20 | **81.2** | _72.8_ | 72.6 | 46.4 ± 4.4 | 46.6 ± 2.1 | 47.7 ± 2.0 | 58.2 ± 2.8 | 33.5 ± 2.0 | 68.6 | 39.2 | 35.9 ± 0.1 |
| COIL100 | **80.1** | 66.8 | _70.0_ | 44.6 ± 4.2 | 46.6 ± 1.5 | 50.1 ± 1.2 | 56.1 ± 1.4 | 16.7 ± 0.8 | 61.4 | 14.2 | 0.2 |
| cmu_faces | 60.2 | 56.6 | **66.5** | 8.6 ± 3.1 | 37.1 ± 4.1 | 34.2 ± 2.1 | 53.2 ± 4.7 | 38.5 ± 2.9 | _61.6_ | 0.7 | 0.6 |
| OptDigits | 55.3 | **77.0** | **77.0** | 40.9 ± 3.5 | 20.9 ± 2.3 | 18.1 ± 2.4 | 61.3 ± 6.6 | 14.4 ± 4.1 | _74.6 ± 2.4_ | 63.2 | 0.0 |
| USPS | 33.7 | 29.3 | 29.3 | 12.0 ± 1.7 | 8.7 ± 1.0 | 11.2 ± 1.5 | _52.3 ± 1.7_ | 2.9 ± 0.9 | **63.9** | 0.0 | 21.0 |
| MNIST | 19.7 | 41.7 | _46.0_ | 11.1 ± 1.7 | 5.4 ± 0.6 | 5.4 ± 0.6 | 36.9 ± 1.0 | 1.3 ± 0.4 | **52.7** | 0.0 | - |

- `DC = DCTree`, `CT = CoverTree`
- `Stab. = Stability`, `MoE = MedianOfElbows`, `Elb. = Elbow`
- Competitors: [k-means](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html), [SCAR](https://github.com/SpectralClusteringAcceleratedRobust/SCAR), [Ward](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html), [AMD-DBSCAN](https://github.com/AlexandreWANG915/AMD-DBSCAN), [DPC](https://github.com/colinwke/dpca)


## License
The project is licensed under the BSD 3-Clause License (see [LICENSE.txt](https://github.com/pasiweber/SHiP-framework/blob/main/LICENSE.txt)).


## References
[1] [Connecting the Dots -- Density-Connectivity Distance unifies DBSCAN, k-Center and Spectral Clustering](https://epub.ub.uni-muenchen.de/123737/)
<br>
[2] [HST+: An Efficient Index for Embedding Arbitrary Metric Spaces](https://ieeexplore.ieee.org/document/9458703/)
([Github](https://github.com/yzengal/ICDE21-HST))
<br>
[3] [mlpack 4: a fast, header-only C++ machine learning library](https://joss.theoj.org/papers/10.21105/joss.05026) 
([Github](https://github.com/mlpack/mlpack))
