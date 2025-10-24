#pragma once

#include <memory>
#include <vector>

#include "../ultrametric_tree_structure.hpp"


struct MSTEdge {
    unsigned long long src;
    unsigned long long dst;
    double weight;
};

std::tuple<arma::mat, arma::vec> compute_mutual_reachability_dists(const arma::mat& data, unsigned long long k);

std::vector<MSTEdge> calc_mst(unsigned long long n, double* data);

std::shared_ptr<UltrametricTreeNode> constructHierarchy(std::vector<MSTEdge> edges, double eps);

std::shared_ptr<UltrametricTreeNode> construct_dc_tree(std::vector<std::vector<double>>& data, unsigned long long k, bool relaxed = false);
