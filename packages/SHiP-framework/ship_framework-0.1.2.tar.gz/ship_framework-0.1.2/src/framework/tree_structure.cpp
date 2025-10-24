#include "tree_structure.hpp"

#include <framework/partitioning/elbow_methods.hpp>
#include <framework/partitioning/tree_partitioning.hpp>
#include <framework/tree_construction/ultrametric_tree_structure.hpp>
#include <pch.hpp>


Tree::Tree(std::shared_ptr<Node> root, std::vector<std::vector<double>>& data, UltrametricTreeType tree_type, long long hierarchy, const std::unordered_map<std::string, std::string>& config) : tree_type(tree_type), hierarchy(hierarchy), config(config) {
    // Annotate tree to get the k_clustering for the current hierarchy
    this->annotate_tree(root, data);

    if (hierarchy == 0) {
        this->root = root;
    } else {
        // Build the new tree from the annotated information
        this->root = create_centroids_hierarchy();
    }

    assign_node_sizes(this->root);
    bool is_tree_valid = check_tree_validity<Node>(this->root);
    if (!is_tree_valid) {
        LOG_ERROR << "Tree is invalid";
        throw std::invalid_argument("Tree is invalid");
    }

    this->setup_fast_index();
    this->compute_sorted_nodes();
    this->compute_sorted_costs();

    if (hierarchy == 0) {
        this->assign_nodes_their_k_values();
    }
}


/*
    Function that traverses the tree in postfix order (left child first, then right child). For every leaf node we store its id in the `index_order` array. Each node will also get a `low` and `high` pointer id which refers to the corresponding area in the `index_order` array.
*/
void Tree::setup_fast_index() {
    this->index_order.resize(this->root->size);

    long long ctr = 0;
    std::vector<std::pair<std::shared_ptr<Node>, bool>> stack;
    stack.emplace_back(root, false);
    while (!stack.empty()) {
        auto [node, processed_children] = stack.back();
        stack.pop_back();
        if (node->children.empty()) {  // leaf
            node->low = ctr;
            node->high = ctr;
            this->index_order[ctr] = node->id;
            ctr++;
        } else {
            if (!processed_children) {
                // This ctr index will be used by leftmost child
                node->low = ctr;
                stack.emplace_back(node, true);
                for (auto it = node->children.rbegin(); it != node->children.rend(); ++it) {
                    stack.emplace_back(*it, false);
                }
            } else {
                // ctr is what was returned by rightmost child (but it used ctr-1 as its own index)
                node->high = ctr - 1;
            }
        }
    }
}


/*
    Makes a list of the nodes and of the costs. Nodes used for computing the cut, and costs for the elbow.
    Also adds the level for each node to ensure correct ordering for ties.
*/
void Tree::compute_sorted_nodes() {
    std::vector<std::shared_ptr<Node>> stack;
    stack.push_back(this->root);
    this->sorted_nodes.reserve(this->root->size);

    while (!stack.empty()) {
        auto node = stack.back();
        stack.pop_back();
        this->sorted_nodes.push_back(node);
        for (std::shared_ptr<Node> child : node->children) {
            stack.push_back(child);
        }
    }
    std::sort(this->sorted_nodes.begin(), this->sorted_nodes.end(), [](const std::shared_ptr<Node>& a, const std::shared_ptr<Node>& b) {
        return *a > *b;
    });
}

void Tree::compute_sorted_costs() {
    this->costs.clear();
    this->costs.reserve(this->cost_decreases.size() + 1);
    double curr_cost = this->max_cost;
    costs.push_back(curr_cost);
    for (double cost_decrease : this->cost_decreases) {
        curr_cost -= cost_decrease;
        costs.push_back(curr_cost);
    }
}

/*
    Takes as input the sorted list of nodes
*/
void Tree::assign_nodes_their_k_values() {
    this->sorted_nodes[0]->k = 1;  // Annotate the root with 1
    long long k = 2;

    for (std::shared_ptr<Node> node : this->sorted_nodes) {
        if (node->children.empty()) {  // Ignore leaves (both for ultrametric and relaxed ultrametric)
            continue;
        } else {
            long long i = 0;
            for (std::shared_ptr<Node> child : node->children) {
                if (i == 0) {
                    child->k = k;
                } else {
                    child->k = k;
                    k++;
                }
                i++;
            }
        }
    }
}


std::vector<std::vector<double>> Tree::get_distance_matrix() {
    unsigned long long n = this->root->size;
    std::vector<std::vector<double>> distance_matrix(n, std::vector<double>(n));
    auto& nodes = this->sorted_nodes;

#pragma omp parallel for schedule(dynamic)
    for (int idx = 0; idx < static_cast<int>(nodes.size()); ++idx) {
        auto node = nodes[idx];
        for (size_t i = 0; i < node->children.size(); ++i) {
            for (size_t j = i + 1; j < node->children.size(); ++j) {
                for (long long left = node->children[i]->low; left <= node->children[i]->high; ++left) {
                    for (long long right = node->children[j]->low; right <= node->children[j]->high; ++right) {
                        size_t u = this->index_order[left];
                        size_t v = this->index_order[right];
                        distance_matrix[u][v] = distance_matrix[v][u] = node->cost;
                    }
                }
            }
        }
    }
    return distance_matrix;
}


// Function to convert UltrametricTreeNode to Node
std::shared_ptr<Node> convertUltrametricTreeNodeToNode(std::shared_ptr<UltrametricTreeNode> ultrametricTreeRootNode) {
    if (!ultrametricTreeRootNode) return nullptr;

    // Stack to hold UltrametricTreeNode and corresponding parent Node
    std::vector<std::pair<std::shared_ptr<UltrametricTreeNode>, std::shared_ptr<Node>>> stack;
    std::shared_ptr<Node> root = std::make_shared<Node>(ultrametricTreeRootNode->id, ultrametricTreeRootNode->cost);
    root->size = ultrametricTreeRootNode->size;
    stack.emplace_back(ultrametricTreeRootNode, root);

    while (!stack.empty()) {
        auto [currentUltrametricTreeNode, currentNode] = stack.back();
        stack.pop_back();

        currentNode->children.reserve(currentUltrametricTreeNode->children.size());
        // Iterate through all children of the current UltrametricTreeNode
        for (const auto& child : currentUltrametricTreeNode->children) {
            // Create a new Node for each child
            auto newNode = std::make_shared<Node>(child->id, child->cost, std::vector<std::shared_ptr<Node>>(), currentNode);
            root->size = ultrametricTreeRootNode->size;
            currentNode->children.push_back(newNode);

            // Push the child and the new Node to the stack
            stack.emplace_back(child, newNode);
        }
    }

    return root;
}
