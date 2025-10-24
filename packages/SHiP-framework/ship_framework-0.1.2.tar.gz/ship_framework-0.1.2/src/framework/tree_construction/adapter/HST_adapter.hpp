#pragma once

#include <memory>
#include <vector>

#include "../HST/HST_opt.hpp"
#include "../ultrametric_tree_structure.hpp"

Node_t *build_HST(std::vector<std::vector<double>> &data, const std::unordered_map<std::string, std::string> &config = {});
std::shared_ptr<UltrametricTreeNode> convert_from_HST(Node_t *root_HST);
UltrametricTree build_from_HST(std::vector<std::vector<double>> &data, const std::unordered_map<std::string, std::string> &config = {});
