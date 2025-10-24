#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <framework/SHiP.hpp>
#include <framework/partitioning/available_partitionings.hpp>
#include <framework/tree_construction/available_trees.hpp>
#include <pch.hpp>

#include "helper.hpp"
#include "classes/enum_types.cpp"
#include "classes/tree_structure.cpp"
#include "classes/SHiP.cpp"

namespace py = pybind11;


PYBIND11_MODULE(SHiP, m) {
    m.doc() = R"pbdoc(
        Python bindings for the SHiP (Similarity-Hierarchical-Partitioning) clustering framework.

        SHiP is a flexible and modular clustering library that constructs and analyzes similarity-based
        hierarchical structures for data clustering. It is the official implementation of the methods
        introduced in the paper *Ultrametric Cluster Hierarchies: I Want 'em All!*

        | **Overview**
        | The SHiP framework operates in three main stages:

        | 1. **Similarity Tree Construction**  
        |    Build a tree that encodes proximity relationships between data points.

        | 2. **Hierarchy Construction**  
        |    Derive clustering hierarchies (e.g., $k$-means, $k$-median) from the tree.

        | 3. **Partitioning**  
        |    Select and apply a partitioning method (e.g., Elbow, fixed-K) to extract flat clusters.

        SHiP allows users to mix and match components (trees, hierarchies, partitioning objectives)
        for fully customized clustering workflows.

        **Example**

        .. code-block:: python
    
            from SHiP import SHiP
    
            ship = SHiP(data=data_points, treeType="DCTree")
            labels = ship.fit_predict(hierarchy=2, partitioningMethod="Elbow")

        | **Implementation**
        | The core of the project is implemented in C++, with Python bindings provided via pybind11.
    )pbdoc";


    ///// Enum Types /////
    bind_UltrametricTreeTypes(m);
    bind_PartitioningMethods(m);
    bind_Logger(m);


    ///// Classes /////
    bind_SHiP(m);
    bind_Tree(m);
    bind_Node(m);
}
