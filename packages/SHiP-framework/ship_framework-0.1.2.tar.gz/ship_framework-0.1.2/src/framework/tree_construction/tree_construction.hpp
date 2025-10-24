#pragma once

#include <string>
#include <unordered_map>
#include <vector>

#include "available_trees.hpp"
#include "ultrametric_tree_structure.hpp"


// Construct an UltrametricTree given the `tree_type` string
UltrametricTree constructUltrametricTree(std::vector<std::vector<double>>& data, UltrametricTreeType tree_type = UltrametricTreeType::DCTree, const std::unordered_map<std::string, std::string> &config = {});
