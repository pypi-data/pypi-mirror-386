#pragma once

#include "../available_trees.hpp"
#include "../ultrametric_tree_structure.hpp"


template <typename TreeType>
std::shared_ptr<UltrametricTreeNode> convert_from_MLPackTree(const TreeType &root_MLPackTree, std::vector<size_t> &oldFromNew);
std::shared_ptr<UltrametricTreeNode> convert_from_MLPackTree(std::vector<std::vector<double>> &data, UltrametricTreeType tree_type, const std::unordered_map<std::string, std::string> &config = {});
UltrametricTree build_from_MLPackTree(std::vector<std::vector<double>> &data, UltrametricTreeType tree_type, const std::unordered_map<std::string, std::string> &config = {});
