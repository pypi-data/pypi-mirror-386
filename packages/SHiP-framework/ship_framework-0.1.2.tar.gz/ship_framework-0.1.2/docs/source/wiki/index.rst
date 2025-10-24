Wiki
====


Available Trees
---------------
The SHiP framework supports a variety of **ultrametric similarity tree types**, which form the basis for hierarchy construction. Each tree type encapsulates a specific strategy for representing pairwise similarity across the dataset.

The enum below lists all available tree types supported in the framework:

.. doxygenenum:: UltrametricTreeType
   :project: SHiP
   :no-link:

----

.. _dc-dist:
| [1] *Based on the paper:*
| Anna Beer, Andrew Draganov, Ellen Hohma, Philipp Jahn, Christian M.M. Frey, Ira Assent.
| **Connecting the Dots -- Density-Connectivity Distance unifies DBSCAN, k-Center and Spectral Clustering.**
| Proceedings of the 29th ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD), 2023.

----

.. _hst:
| [2] *Adapted from the original codebase:* `ICDE21-HST <https://github.com/yzengal/ICDE21-HST>`_ *and is based on the paper:*
| Yuxiang Zeng, Yongxin Tong, Lei Chen.
| **HST+: An Efficient Index for Embedding Arbitrary Metric Spaces.**
| IEEE International Conference on Data Engineering (ICDE), 2021.

----

.. _mlpack:
| [3] *Implemented in the mlpack 4 C++ machine learning library:*
| Ryan R. Curtin, Marcus Edel, Omar Shrit, Shubham Agrawal, Suryoday Basak, James J. Balamuta, Ryan Birmingham, Kartik Dutt, Dirk Eddelbuettel, Rishabh Garg, Shikhar Jaiswal, Aakash Kaushik, Sangyeon Kim, Anjishnu Mukherjee, Nanubala Gnana Sai, Nippun Sharma, Yashwant Singh Parihar, Roshan Swain, Conrad Sanderson.
| **mlpack 4: a fast, header-only C++ machine learning library**
| Journal of Open Source Software, 2023.
| See: https://doi.org/10.21105/joss.05026


Available Hierarchies
----------------------
Once a similarity tree is built, it can be transformed into a **clustering hierarchy**. These hierarchies generalize well-known clustering paradigms such as $k$-means and $k$-median, enabling fine-grained control over how cluster centroids and merges are computed.

We support all possible $(k,z)$-hierarchies, allowing flexibility in choosing the most suitable hierarchy for a given dataset.

  - $z = 0$ → $k$-center (actually in theory: $z = ∞$, but in this implementation we use 0 for $∞$)
  - $z = 1$ → $k$-median
  - $z = 2$ → $k$-means
  - ...


Available Partitioning Methods
------------------------------
The SHiP framework provides multiple **partitioning methods** to extract flat clusterings from hierarchies. Each method corresponds to a specific partitioning objective or heuristic, such as fixed-$k$, elbow detection, and also function-based selection strategies, as e.g., the HDBSCAN stability function.

The enum below shows all available partitioning strategies:

.. doxygenenum:: PartitioningMethod
   :project: SHiP
   :no-link:


----

*Customization and Composition*
-------------------------------

Each of the above components — trees, hierarchies, and partitioning strategies — can be **independently selected and composed**. This enables flexible experimentation and tailored clustering behavior for a wide range of data types and analysis goals.

Example:

.. code-block:: python

   from SHiP import SHiP
   from SHiP.ultrametric_tree import UltrametricTreeType
   from SHiP.partitioning import PartitioningMethod

   ship = SHiP(data=my_data, treeType=UltrametricTreeType.DCTree)
   labels = ship.fit_predict(hierarchy=2, partitioningMethod=PartitioningMethod.Elbow)


.. toctree::
   :maxdepth: 1
   :caption: Contents:
