#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <framework/tree_structure.hpp>
#include <pch.hpp>

namespace py = pybind11;


inline void bind_Node(py::module_ &m) {
    py::class_<Node, std::shared_ptr<Node>>(m, "Node")
        // Expose fields
        .def_readonly("id", &Node::id,
                      R"pbdoc(
    Unique identifier of the node.

    Typically corresponds to the merge order or original data point index.
    )pbdoc")

        .def_readonly("cost", &Node::cost,
                      R"pbdoc(
    Cost (distance or merging cost) at this node.

    Represents the dissimilarity between the merged clusters.
    )pbdoc")

        .def_readonly("children", &Node::children,
                      R"pbdoc(
    List of child nodes.

    For leaf nodes, this list is empty. For internal nodes, it contains two or more children.
    )pbdoc")

        .def_readonly("parent", &Node::parent,
                      R"pbdoc(
    Parent node in the tree hierarchy.

    Points to the node resulting from merging this node with a sibling.
    )pbdoc")

        .def_readonly("size", &Node::size,
                      R"pbdoc(
    Number of original data points (leave nodes) in the subtree rooted at this node.
    )pbdoc")

        .def_readonly("low", &Node::low,
                      R"pbdoc(
    Start index in the `index_order` array.

    Used to efficiently extract all leave nodes of this node.
    )pbdoc")

        .def_readonly("high", &Node::high,
                      R"pbdoc(
    End index in the `index_order` array.

    Used to efficiently extract all leave nodes of this node.
    )pbdoc")

        .def_readonly("level", &Node::level,
                      R"pbdoc(
    Depth of the node in the tree.

    The root has the lowest level 0.
    )pbdoc")

        // Comparison operators
        .def(
            "__lt__", [](const Node &self, const Node &other) { return self < other; },
            R"pbdoc(
    Less-than comparison based on node cost.

    Enables sorting nodes by merge cost.
    )pbdoc")

        .def(
            "__gt__", [](const Node &self, const Node &other) { return self > other; },
            R"pbdoc(
    Greater-than comparison based on node cost.

    Enables sorting nodes by merge cost.
    )pbdoc")

        // to_json method
        .def("to_json", &Node::to_json,
             py::arg("fast_index") = false,
             R"pbdoc(
     Serialize the node to a JSON-compatible structure.

     Parameters:
        fast_index (bool, optional): Whether to include additional indexing information for faster leave node extracting. Defaults to `False`.

    Returns:
        str: The JSON-encoded representation of the tree.
     )pbdoc");
}


inline pybind11::array_t<double> get_distance_matrix_np(Tree &tree) {
    size_t n = tree.root->size;
    auto result = pybind11::array_t<double>({n, n});
    auto r = result.mutable_unchecked<2>();  // for fast access

#pragma omp parallel for schedule(dynamic)
    for (const auto &node : tree.sorted_nodes) {
        for (size_t i = 0; i < node->children.size(); ++i) {
            for (size_t j = i + 1; j < node->children.size(); ++j) {
                for (long long left = node->children[i]->low; left <= node->children[i]->high; ++left) {
                    for (long long right = node->children[j]->low; right <= node->children[j]->high; ++right) {
                        size_t u = tree.index_order[left];
                        size_t v = tree.index_order[right];
                        r(u, v) = r(v, u) = node->cost;
                    }
                }
            }
        }
    }
    return result;
}


inline void bind_Tree(py::module_ &m) {
    py::class_<Tree, std::shared_ptr<Tree>>(m, "Tree")

        // Expose fields (read access only)
        .def_readonly("root", &Tree::root,
                      R"pbdoc(
    Root node of the tree.

    This is the entry point to traverse the full hierarchical structure.
    )pbdoc")

        .def_readonly("tree_type", &Tree::tree_type,
                      R"pbdoc(
    Used ultrametric tree type.

    Indicates the ultrametric tree type used to build the tree (e.g., DCTree, KDTree).
    )pbdoc")

        .def_readonly("hierarchy", &Tree::hierarchy,
                      R"pbdoc(
    Used hierarchy of the tree.

    Which `z` was used to build the tree (e.g., z=0 ($k$-center), z=1 ($k$-median), z=2 ($k$-means)).
    )pbdoc")

        .def_readonly("config", &Tree::config,
                      R"pbdoc(
    Configuration dictionary passed during tree creation.

    Contains algorithm-specific parameters and settings.
    )pbdoc")

        .def_readonly("index_order", &Tree::index_order,
                      R"pbdoc(
    Ordering of the leave nodes according to the tree structure.

    Maps original data point indices to their position in the tree (left to right).
    )pbdoc")

        .def_readonly("sorted_nodes", &Tree::sorted_nodes,
                      R"pbdoc(
    List of tree nodes sorted by merge cost.

    Useful for analyzing the tree structure and extracting intermediate clusters.
    )pbdoc")

        .def_readonly("costs", &Tree::costs,
                      R"pbdoc(
    List of merge costs at each step in the tree.

    Encodes the cost at which each merge occurred.
    )pbdoc")

        .def_readonly("cost_decreases", &Tree::cost_decreases,
                      R"pbdoc(
    Cost decreases between successive merges.

    Encodes the cost decreases at each merging step (can be lower than `n`).
    )pbdoc")


        // Expose methods
        .def("get_elbow_k", &Tree::get_elbow_k,
             py::arg("triangle") = true,
             R"pbdoc(
    Compute the optimal number of clusters `k` using the Elbow method.

    Parameters:
        triangle (bool, optional): Whether to use the new triangle Elbow method. Defaults to `True`.

    Returns:
        int: The estimated optimal number of clusters.
    )pbdoc")

        .def(
            "distance_matrix", [](Tree &self) {
                return get_distance_matrix_np(self);
            },
            R"pbdoc(
    Generate the ultrametric distance matrix from the tree.

    The matrix is symmetric and encodes the pairwise distances 
    between all data points based on their lowest common ancestor 
    in the hierarchy.

    Returns:
        np.array: A 2D distance matrix.

    Notes
    -----
    This function does not care about the exact structure of the tree, hence for faster speed one can change the `tiebreaker_method` to "random":

    .. code-block:: python

        from SHiP import SHiP

        ship = SHiP(data=data_points, treeType="DCTree", config={"tiebreaker_method": "random"})
        dists = ship.get_tree().distance_matrix()

    Note that using the `get_tree()` method without specifying the hierarchy will always return the base tree (`hierarchy=0`).
    )pbdoc")

        .def("to_json", &Tree::to_json, py::arg("fast_index") = false,
             R"pbdoc(
    Serialize the tree structure to a JSON string.

    Parameters:
        fast_index (bool, optional): Whether to include additional indexing information for faster leave node extracting. Defaults to `False`.

    Returns:
        str: The JSON-encoded representation of the tree.
    )pbdoc");
}
