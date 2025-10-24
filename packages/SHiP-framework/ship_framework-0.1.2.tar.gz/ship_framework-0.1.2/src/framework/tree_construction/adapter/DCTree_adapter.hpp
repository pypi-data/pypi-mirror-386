#pragma once

#include <memory>
#include <vector>

#include "../DCTree/dc_dist_computation.hpp"
#include "../ultrametric_tree_structure.hpp"


std::shared_ptr<UltrametricTreeNode> build_DCTree(std::vector<std::vector<double>> &data, const std::unordered_map<std::string, std::string> &config = {});
std::shared_ptr<UltrametricTreeNode> convert_from_DCTree(std::shared_ptr<UltrametricTreeNode> &root);
UltrametricTree build_from_DCTree(std::vector<std::vector<double>> &data, const std::unordered_map<std::string, std::string> &config = {});
