C++ API
=======

Welcome to the C++ API documentation of the SHiP (Similarity-Hierarchical-Partitioning) framework.

This section provides detailed insights into the internal components of the C++ implementation, including class definitions, method details, enums, and helper functions. If you're extending or interfacing with the core C++ codebase, this is the place to explore.

The SHiP framework is designed with modularity and extensibility in mind. Its structure is organized into the following key components:

- **SHiP Core**

  Contains the main entry points and orchestration logic for the SHiP framework. This includes core configuration, parameter handling, and coordination of the tree construction, hierarchy generation, and partitioning stages.

- **Tree Construction**

  Implements various algorithms to build similarity trees from data. These trees represent the foundational structure used to derive cluster hierarchies.

- **Hierarchy**

  Responsible for constructing clustering hierarchies from similarity trees. This layer enables different clustering paradigms (e.g., $k$-means, $k$-median) through hierarchical interpretations.

- **Tree Partitioning**

  Provides various objective functions and algorithms to extract flat partitions from hierarchical trees — such as Elbow Method, Silhouette or for a specific K.

- **Helper Methods**

  Includes utility functions, mathematical helpers, logging tools, and type definitions used throughout the framework.


Use the navigation on the left to explore each component in detail. Each section provides both inline documentation (from Doxygen) and structural overviews to help you understand the responsibilities and interfaces of the different parts of the codebase.


.. toctree::
   :maxdepth: 1
   :caption: Source Files

   framework/SHiP
   framework/tree_construction
   framework/hierarchy
   framework/partitioning
   helper
