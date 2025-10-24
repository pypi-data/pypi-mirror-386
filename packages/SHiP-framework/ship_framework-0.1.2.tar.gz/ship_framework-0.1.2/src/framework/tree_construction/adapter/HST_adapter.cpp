#include "HST_adapter.hpp"

#include <pch.hpp>

#include "../available_trees.hpp"


Node_t *build_HST(std::vector<std::vector<double>> &data, const std::unordered_map<std::string, std::string> &config) {
    long long seed = get_config_value(config, "seed", -1);

    constructHST_fast_dp(data, seed);
    calcDists(rt);
    return rt;
}

std::shared_ptr<UltrametricTreeNode> convert_from_HST(Node_t *root_HST) {
    std::vector<std::pair<Node_t *, std::shared_ptr<UltrametricTreeNode>>> stack;
    auto root = std::make_shared<UltrametricTreeNode>(-1, rt->dist);
    for (Node_t *child : root_HST->child) {
        stack.emplace_back(child, root);
    }
    while (!stack.empty()) {
        auto [hst_tree, tree] = stack.back();
        stack.pop_back();
        if (hst_tree->child.empty()) {
            tree->children.push_back(std::make_shared<UltrametricTreeNode>(hst_tree->pid, hst_tree->dist));
        } else {
            auto inter = std::make_shared<UltrametricTreeNode>(-1, hst_tree->dist);
            tree->children.push_back(inter);
            for (Node_t *child : hst_tree->child) {
                stack.emplace_back(child, inter);
            }
        }
    }
    freeMemory_HST();
    return root;
}

UltrametricTree build_from_HST(std::vector<std::vector<double>> &data, const std::unordered_map<std::string, std::string> &config) {
    Node_t *root = build_HST(data, config);
    std::shared_ptr<UltrametricTreeNode> tree = convert_from_HST(root);
    return UltrametricTree{tree, UltrametricTreeType::HST, config};
}
