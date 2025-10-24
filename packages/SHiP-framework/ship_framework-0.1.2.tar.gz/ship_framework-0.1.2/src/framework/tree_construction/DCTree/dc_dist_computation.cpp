#include "dc_dist_computation.hpp"

#include "union_find.hpp"


typedef struct Subset {
    unsigned long long parent;
    unsigned long long rank;
    std::shared_ptr<UltrametricTreeNode> root_node;
} Subset;

typedef struct Edge {
    long long src;
    long long dst;
} Edge;


// This does path compression while finding the root, so that next time i is queried this will go a lot faster.
unsigned long long findParentIdx(std::vector<Subset> &subsets, unsigned long long i) {
    while (subsets[i].parent != i) {
        subsets[i].parent = subsets[subsets[i].parent].parent;  // This is faster than complete path compression in each call
        i = subsets[i].parent;
    }
    return subsets[i].parent;
}

void unifySets(std::vector<Subset> &subsets, unsigned long long x, unsigned long long y) {
    unsigned long long xRoot = findParentIdx(subsets, x);
    unsigned long long yRoot = findParentIdx(subsets, y);

    if (xRoot != yRoot) {
        if (subsets[xRoot].rank > subsets[yRoot].rank) {
            subsets[yRoot].parent = xRoot;
        } else if (subsets[yRoot].rank > subsets[xRoot].rank) {
            subsets[xRoot].parent = yRoot;
        } else {
            subsets[yRoot].parent = xRoot;
            subsets[xRoot].rank++;
        }
    }
}

// <= Means that we sort in increasing order.
bool compareEdgesByCost(const MSTEdge e1, const MSTEdge e2) {
    return e1.weight <= e2.weight;
}


std::tuple<arma::mat, arma::vec> compute_mutual_reachability_dists(const arma::mat &data, unsigned long long k) {
    if (k <= 1) k = 2;

    long long n = data.n_cols;
    arma::mat dists(n, n, arma::fill::none);
#pragma omp parallel for schedule(static)
    for (long long i = 0; i < n; ++i) {
        dists(i, i) = 0.0;
    }

    // Stage 1: Parallel fill upper triangle (j > i)
#pragma omp parallel for schedule(guided)
    for (long long i = 0; i < n; ++i) {
        for (long long j = i + 1; j < n; ++j) {
            double dist = arma::norm(data.col(i) - data.col(j), 2);
            dists(i, j) = dist;
        }
    }

    // Stage 2: Compute core distances
    arma::vec core_dists(n);
#pragma omp parallel for schedule(static)
    for (long long i = 0; i < n; ++i) {
        std::vector<double> knn_dists;
        knn_dists.reserve(n - 1);

        for (long long j = 0; j < i; ++j) {
            knn_dists.push_back(dists(j, i));
        }
        for (long long j = i + 1; j < n; ++j) {
            knn_dists.push_back(dists(i, j));
        }

        std::nth_element(knn_dists.begin(), knn_dists.begin() + (k - 2), knn_dists.end());
        core_dists[i] = knn_dists[k - 2];
    }

    // Stage 3: Parallel fill lower triangle (j < i)
#pragma omp parallel for schedule(guided)
    for (long long i = 0; i < n; ++i) {
        for (long long j = i + 1; j < n; ++j) {
            dists(j, i) = dists(i, j);
        }
    }

    // Stage 4: Compute mutual-reachability distances
#pragma omp parallel for schedule(static)
    for (long long j = 0; j < n; ++j) {
        dists.col(j) = arma::max(dists.col(j), core_dists);
    }
#pragma omp parallel for schedule(static)
    for (long long i = 0; i < n; ++i) {
        dists.row(i) = arma::max(dists.row(i), core_dists.t());
    }
#pragma omp parallel for schedule(static)
    for (long long i = 0; i < n; ++i) {
        dists(i, i) = 0.0;
    }
    return {dists, core_dists};
}


std::vector<MSTEdge> calc_mst(arma::mat &mut_dists) {
    unsigned long long n = mut_dists.n_cols;
    std::vector<Subset> subsets(n);
    std::vector<Edge> nearest(n);
    std::vector<long long> rootParent(n);
    std::vector<MSTEdge> mstEdges(n - 1);

    for (unsigned long long i = 0; i < n; i++) {
        subsets[i].parent = i;
        subsets[i].rank = 0;
        rootParent[i] = -1;
        nearest[i].src = -1;
    }

    unsigned long long noOfTrees = n;
    unsigned long long v = 0;

    while (noOfTrees > 1) {
        for (unsigned long long i = 0; i < n; i++) {
            for (unsigned long long j = i + 1; j < n; j++) {
                if (mut_dists(j, i) != 0) {
                    // if 2 elements have the same parent at a point, then they will always have the same parent so
                    // no need to compute
                    if (rootParent[i] != -1 && (rootParent[i] == rootParent[j])) {
                        continue;
                    }
                    // find parent
                    unsigned long long root1 = findParentIdx(subsets, i);
                    unsigned long long root2 = findParentIdx(subsets, j);

                    // ignore if the same parent (same disjoint set)
                    if (root1 == root2) {
                        rootParent[i] = (long long)root1;
                        rootParent[j] = (long long)root2;
                        continue;
                    }

                    if (nearest[root1].src == -1 || mut_dists(nearest[root1].dst, nearest[root1].src) > mut_dists(j, i)) {
                        nearest[root1].src = (long long)i;
                        nearest[root1].dst = (long long)j;
                    }
                    if (nearest[root2].src == -1 || mut_dists(nearest[root2].dst, nearest[root2].src) > mut_dists(j, i)) {
                        nearest[root2].src = (long long)i;
                        nearest[root2].dst = (long long)j;
                    }
                }
            }
        }

        for (unsigned long long i = 0; i < n; i++) {
            if (nearest[i].src == -1) {
                continue;
            }

            unsigned long long root1 = findParentIdx(subsets, nearest[i].src);
            unsigned long long root2 = findParentIdx(subsets, nearest[i].dst);

            if (root1 == root2) {
                nearest[i].src = -1;
                continue;
            }

            mstEdges[v].src = nearest[i].src;
            mstEdges[v].dst = nearest[i].dst;
            mstEdges[v].weight = mut_dists(nearest[i].dst, nearest[i].src);
            nearest[i].src = -1;

            // unify trees/disjoint sets
            unifySets(subsets, root1, root2);
            noOfTrees--;
            v++;
        }
    }
    return mstEdges;
}


std::shared_ptr<UltrametricTreeNode> constructHierarchy(std::vector<MSTEdge> &mst_edges, double eps = 1e-9) {
    std::sort(mst_edges.begin(), mst_edges.end(), compareEdgesByCost);  // Sort edges in ascending order

    unsigned long long n = mst_edges.size() + 1;  // Number of data points
    UnionFind union_find(n);                      // Initialize n nodes with UnionFind
    unsigned long long idx = n;                   // Starting index for new nodes
    std::shared_ptr<UltrametricTreeNode> node;    // Root node

    std::vector<std::shared_ptr<UltrametricTreeNode>> root;  // Pointer to their current root node for all data points
    root.reserve(n);
    for (unsigned long long id = 0; id < n; ++id) {
        root.emplace_back(std::make_shared<UltrametricTreeNode>(id, 0));  // Initialize Nodes with id
    }

    // Iterate over the edges to build the tree
    for (const auto &edge : mst_edges) {
        long long src = edge.src;
        long long dst = edge.dst;
        double weight = edge.weight;

        std::shared_ptr<UltrametricTreeNode> src_root = root[union_find.find(src)];  // Find root of i
        std::shared_ptr<UltrametricTreeNode> dst_root = root[union_find.find(dst)];  // Find root of j

        if ((src_root != nullptr && abs(src_root->cost - weight) < eps) && (dst_root != nullptr && abs(dst_root->cost - weight) < eps)) {
            // If both src_root and dst_root have the same weight (cost) as the current edge,
            // merge both nodes, i.e., put all children of one root under the other one, and delete the former
            long long root_idx = union_find.union_set(src, dst);
            if ((src_root->children).size() < (dst_root->children).size()) {
                // If src_root has less childred than dst_root, put all children of src_root under dst_root
                for (std::shared_ptr<UltrametricTreeNode> &node : src_root->children) {
                    dst_root->children.push_back(node);
                }
                // delete src_root;
                root[root_idx] = dst_root;
            } else {
                // Put all children of dst_root under src_root
                for (std::shared_ptr<UltrametricTreeNode> &node : dst_root->children) {
                    src_root->children.push_back(node);
                }
                // delete dst_root;
                root[root_idx] = src_root;
            }
        } else if (src_root != nullptr && abs(src_root->cost - weight) < eps) {
            // Otherwise, if only src_root has the same weight (cost) as the current edge,
            // put dst_root under src_root
            src_root->children.push_back(dst_root);
            long long root_idx = union_find.union_set(src, dst);
            root[root_idx] = src_root;
        } else if (dst_root != nullptr && abs(dst_root->cost - weight) < eps) {
            // Same as previous case, but with dst_root has the same weight (cost) as the current edge
            dst_root->children.push_back(src_root);
            long long root_idx = union_find.union_set(src, dst);
            root[root_idx] = dst_root;
        } else {
            // Else all weights are different, hence we create a new node connecting the two roots
            node = std::make_shared<UltrametricTreeNode>(idx, weight);
            node->children.push_back(src_root);
            node->children.push_back(dst_root);
            long long root_idx = union_find.union_set(src, dst);
            root[root_idx] = node;
            idx++;
        }
    }
    return node;  // Return the root of the constructed hierarchy
}



/*
    Adds the core distances as values in the leaves.
*/
void relax_dc_tree(std::shared_ptr<UltrametricTreeNode> &tree, arma::vec &cdists) {
    if (tree->children.empty()) {
        tree->cost = cdists[tree->id];
    } else {
        for (std::shared_ptr<UltrametricTreeNode> &child : tree->children) {
            relax_dc_tree(child, cdists);
        }
    }
}


// k is minPts for core dists
std::shared_ptr<UltrametricTreeNode> construct_dc_tree(std::vector<std::vector<double>> &data, unsigned long long k, bool relaxed) {
    unsigned long long n = data.size();
    unsigned long long dims = data[0].size();

    arma::mat arma_data(dims, n);  // Armadillo allocates column-major
    for (unsigned long long i = 0; i < n; ++i) {
        for (unsigned long long j = 0; j < dims; ++j) {
            arma_data(j, i) = data[i][j];  // Armadillo allocates column-major
        }
    }

    auto [mut_dists, core_dists] = compute_mutual_reachability_dists(arma_data, k);
    std::vector<MSTEdge> edges = calc_mst(mut_dists);
    std::shared_ptr<UltrametricTreeNode> root = constructHierarchy(edges);

    // If relaxed (ultrametric), we directly add the core distances into the leaves as the distances to themselves.
    if (relaxed) {
        relax_dc_tree(root, core_dists);
    }

    return root;
}
