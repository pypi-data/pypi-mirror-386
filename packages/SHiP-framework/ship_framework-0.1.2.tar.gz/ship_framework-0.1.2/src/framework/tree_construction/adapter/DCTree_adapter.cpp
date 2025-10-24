#include "DCTree_adapter.hpp"

#include <pch.hpp>

#include "../available_trees.hpp"


std::shared_ptr<UltrametricTreeNode> build_DCTree(std::vector<std::vector<double>> &data, const std::unordered_map<std::string, std::string> &config) {
    long long min_points = get_config_value_in_range<long long>(config, "min_points", 5, 1, (long long)data.size());

    bool relaxed = get_config_value(config, "relaxed", true);
    return construct_dc_tree(data, min_points, relaxed);
}

std::shared_ptr<UltrametricTreeNode> convert_from_DCTree(std::shared_ptr<UltrametricTreeNode> &root) {
    return root;
}

UltrametricTree build_from_DCTree(std::vector<std::vector<double>> &data, const std::unordered_map<std::string, std::string> &config) {
    std::shared_ptr<UltrametricTreeNode> root = build_DCTree(data, config);
    std::shared_ptr<UltrametricTreeNode> tree = convert_from_DCTree(root);
    return UltrametricTree{tree, UltrametricTreeType::DCTree, config};
}
