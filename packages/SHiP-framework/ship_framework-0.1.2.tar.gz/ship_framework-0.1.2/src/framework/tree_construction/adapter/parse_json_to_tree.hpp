#pragma once

#include "../ultrametric_tree_structure.hpp"


UltrametricTree parse_json_to_tree(const std::unordered_map<std::string, std::string> &config);
