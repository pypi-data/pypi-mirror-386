#include "ultrametric_tree_structure.hpp"

#include <pch.hpp>

#include "available_trees.hpp"


// ------------------------- //
// UltrametricTree Functions //
// ------------------------- //

UltrametricTree::UltrametricTree(std::shared_ptr<UltrametricTreeNode> root,
                                 UltrametricTreeType tree_type,
                                 const std::unordered_map<std::string, std::string>& config)
    : root(root), tree_type(tree_type), config(config) {
    if (this->root == nullptr) {
        LOG_ERROR << "Tree is empty";
        throw std::invalid_argument("Tree is empty");
    }

    set_parents(this->root);

    bool automatically_fix_same_costs = get_config_value(config, "automatically_fix_same_costs", true);
    bool automatically_increase_too_small_costs = get_config_value(config, "automatically_increase_too_small_costs", false);

    if (automatically_fix_same_costs || automatically_increase_too_small_costs) {
        this->move_childs_with_same_cost_as_parent();
    }
    if (automatically_increase_too_small_costs) {
        this->increase_parent_cost_if_too_small();
    }

    assign_node_sizes(this->root);
    bool is_tree_valid = check_tree_validity<UltrametricTreeNode>(this->root);
    if (!is_tree_valid) {
        LOG_ERROR << "Tree is invalid";
        throw std::invalid_argument("Tree is invalid");
    }
}


void UltrametricTree::move_childs_with_same_cost_as_parent() {
    double eps = 1e-9;
    bool moved_child = false;

    std::vector<std::shared_ptr<UltrametricTreeNode>> stack;
    stack.push_back(this->root);

    while (!stack.empty()) {
        auto node = stack.back();
        stack.pop_back();

        // Push children in reverse order to maintain left-to-right order on processing.
        for (auto it = node->children.rbegin(); it != node->children.rend(); ++it) {
            stack.push_back(*it);
        }

        auto parent = node->parent.lock();
        if (parent == nullptr) {
            // If 'node' is root node
            continue;
        }

        if (std::fabs(parent->cost - node->cost) < eps) {
            // If 'parent->cost' ==  'node->cost'
            if (!moved_child) {
                LOG_INFO << "Equal costs between a node and its parent detected. "
                         << "Try automatic fixing...";
                moved_child = true;
            }

            // Delete 'node' from 'parent->children'
            parent->children.erase(
                std::remove(parent->children.begin(), parent->children.end(), node),
                parent->children.end());

            if (parent->parent.lock() == nullptr) {
                // Need a new root node with higher value than current 'node'.
                this->root = std::make_shared<UltrametricTreeNode>(-1, parent->cost + 10 * eps);
                this->root->children.push_back(parent);
                parent->parent = this->root;
            }
            auto grandparent = parent->parent.lock();
            if (parent->children.empty()) {
                // If 'parent' has no remaining childs -> delete 'parent'
                grandparent->children.erase(
                    std::remove(grandparent->children.begin(), grandparent->children.end(), parent),
                    grandparent->children.end());
            }
            // Insert 'node' into 'grandparent->children'
            grandparent->children.push_back(node);
            node->parent = grandparent;
        }
    }
}


void UltrametricTree::increase_parent_cost_if_too_small() {
    double eps = 1e-9;
    bool increased_cost = false;

    std::vector<std::pair<std::shared_ptr<UltrametricTreeNode>, bool>> stack;
    stack.emplace_back(this->root, false);

    while (!stack.empty()) {
        auto [node, already_seen] = stack.back();
        stack.pop_back();

        if (!already_seen) {
            // First time for this node; push it back as seen, then push all its children
            stack.emplace_back(node, true);
            // Push children in reverse order to maintain left-to-right order on processing.
            for (auto it = node->children.rbegin(); it != node->children.rend(); ++it) {
                stack.emplace_back(*it, false);
            }
        } else {
            auto parent = node->parent.lock();
            if (parent == nullptr) {
                // If 'node' is root node
                continue;
            }

            if (parent->cost < node->cost) {
                // If 'parent->cost' ==  'node->cost'
                if (!increased_cost) {
                    LOG_WARN << "Cost of a parent node is smaller than its child. "
                             << "Try automatic fixing...";
                    increased_cost = true;
                }
                parent->cost = node->cost + 10 * eps;
            }
        }
    }
}
