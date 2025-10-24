#pragma once


#include <fmt/core.h>
#include <simdjson.h>

#include <helper/logger.hpp>
#include <map>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

#include "available_trees.hpp"


struct UltrametricTreeNode : std::enable_shared_from_this<UltrametricTreeNode> {
    long long id;
    double cost;
    std::vector<std::shared_ptr<UltrametricTreeNode>> children;

    // For internal usage only
    std::weak_ptr<UltrametricTreeNode> parent;
    unsigned long long size;

    UltrametricTreeNode(long long id, double cost, std::vector<std::shared_ptr<UltrametricTreeNode>> children = {}) : id(id), cost(cost), children(children){};

    std::string to_json();
    bool from_json(std::string& json);
    bool from_json(simdjson::dom::element root_elem);
};


struct UltrametricTree {
    std::shared_ptr<UltrametricTreeNode> root;
    UltrametricTreeType tree_type;
    std::unordered_map<std::string, std::string> config;

    UltrametricTree(std::shared_ptr<UltrametricTreeNode> root, UltrametricTreeType tree_type, const std::unordered_map<std::string, std::string>& config = {});

    void move_childs_with_same_cost_as_parent();
    void increase_parent_cost_if_too_small();

    std::string to_json();
    bool from_json(std::string& json);
    bool from_json(simdjson::dom::element elem);
};


// Templated functions:
struct Node;

template <typename NodeType>
void set_parents(std::shared_ptr<NodeType> root) {
    std::vector<std::shared_ptr<NodeType>> stack;
    stack.push_back(root);

    while (!stack.empty()) {
        auto curr_node = stack.back();
        stack.pop_back();
        if (curr_node == nullptr) {  // leaf
            continue;
        } else {  // internal node
            // Check that the values of all children are smaller
            for (auto child : curr_node->children) {
                child->parent = curr_node;
                stack.push_back(child);
            }
        }
    }
}


template <typename NodeType>
void assign_node_sizes(std::shared_ptr<NodeType> root) {
    std::vector<std::pair<std::shared_ptr<NodeType>, bool>> stack;
    stack.emplace_back(root, false);

    while (!stack.empty()) {
        auto [node, childrenProcessed] = stack.back();
        stack.pop_back();

        if (childrenProcessed) {
            // All children have been processed, calculate node's size
            unsigned long long size = 0;
            for (std::shared_ptr<NodeType> child : node->children) {
                size += child->size;
            }
            node->size = size == 0 ? 1 : size;  // Leaf node has size 1
        } else {
            // Push node back onto the stack to calculate size after its children are processed
            stack.emplace_back(node, true);

            // Push all children onto the stack for processing
            for (std::shared_ptr<NodeType> child : node->children) {
                stack.emplace_back(child, false);
            }
        }
    }
}


// An (relaxed) ultrametric tree is only valid if all node values are decreasing from the root to the
// leaves, i.e. the value of every node must be smaller than that of its parent node.
template <typename NodeType>
bool check_tree_validity(std::shared_ptr<NodeType> root) {
    unsigned long long n = root->size;

    std::vector<long long> occured_ids(n, 0);
    std::vector<std::shared_ptr<NodeType>> stack;
    stack.push_back(root);

    while (!stack.empty()) {
        auto curr_node = stack.back();
        stack.pop_back();
        if (curr_node->children.empty()) {  // leaf
            if (curr_node->id < 0) {
                LOG_ERROR << "Leave node '" << curr_node->id << "' (" << curr_node->cost << ") "
                          << "has an invalid ID ('" << curr_node->id << "' < 0)";
                return false;
            } else if (curr_node->id >= (long long)n) {
                LOG_ERROR << "Leave node '" << curr_node->id << "' (" << curr_node->cost << ") "
                          << "has an invalid ID ('" << curr_node->id << "' >= n)";
                return false;
            } else {
                occured_ids[curr_node->id]++;
            }
        } else {  // internal node
            // Check that the values of all children are smaller
            for (auto child : curr_node->children) {
                if (child->cost >= curr_node->cost) {
                    LOG_ERROR << "Child '" << child->id << "' (" << child->cost << ") "
                              << " is not smaller than its parent '" << curr_node->id << "' "
                              << "(" << curr_node->cost << ")";
                    return false;
                }
                stack.push_back(child);
            }
        }
    }

    // Check that all leaves have unique ids and are numbered from 0 to n-1
    for (unsigned long long i = 0; i < occured_ids.size(); i++) {
        if (occured_ids[i] != 1) {
            LOG_ERROR << "Tree is missing ID '" << i << "'";
            return false;
        }
    }

    return true;
}
