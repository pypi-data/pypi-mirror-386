#include "SHiP.hpp"

#include <framework/tree_construction/tree_construction.hpp>
#include <pch.hpp>


SHiP::SHiP(std::vector<std::vector<double>>& data,
           UltrametricTreeType tree_type,
           long long hierarchy,
           PartitioningMethod partitioning_method,
           const std::unordered_map<std::string, std::string>& config) : data(data), tree_type(tree_type), hierarchy(hierarchy), partitioning_method(partitioning_method), config(config) {
    auto [tree, tree_construction_runtime] = measure_runtime<std::chrono::microseconds>(
        [this, &data]() {
            return this->construct_base_tree(data);
        });
    this->tree_construction_runtime[0] = tree_construction_runtime;
    trees.emplace(0, tree);
    return;
}

// Methods
void SHiP::fit(std::optional<long long> hierarchy, std::optional<PartitioningMethod> partitioning_method, const std::unordered_map<std::string, std::string>& config) {
    if (hierarchy.has_value()) {
        this->hierarchy = hierarchy.value();
    }
    if (partitioning_method.has_value()) {
        this->partitioning_method = partitioning_method.value();
    }
    this->config.insert(config.begin(), config.end());

    long long tree_construction_runtime_sum_previously = 0;
    for (auto const& [key, runtime] : this->tree_construction_runtime) {
        tree_construction_runtime_sum_previously += runtime;
    }

    auto [labels, partitioning_runtime] = measure_runtime<std::chrono::microseconds>(
        [this]() {
            return this->partitioning();
        });
    this->labels_ = labels;

    long long tree_construction_runtime_sum_after = 0;
    for (auto const& [key, runtime] : this->tree_construction_runtime) {
        tree_construction_runtime_sum_after += runtime;
    }

    long long additional_tree_constructions_runtime = tree_construction_runtime_sum_after - tree_construction_runtime_sum_previously;
    this->partitioning_runtime = partitioning_runtime - additional_tree_constructions_runtime;
}

std::vector<long long> SHiP::fit_predict(std::optional<long long> hierarchy, std::optional<PartitioningMethod> partitioning_method, const std::unordered_map<std::string, std::string>& config) {
    this->fit(hierarchy, partitioning_method, config);
    return this->labels_;
}


// Build tree for given `tree_type`
std::shared_ptr<Tree> SHiP::construct_base_tree(std::vector<std::vector<double>>& data) {
    UltrametricTree ultrametricTree = constructUltrametricTree(data, this->tree_type, this->config);
    std::shared_ptr<Node> root = convertUltrametricTreeNodeToNode(ultrametricTree.root);
    auto tree = std::make_shared<Tree>(root, data, ultrametricTree.tree_type, 0, ultrametricTree.config);
    this->tree_type = tree->tree_type;
    this->config = tree->config;
    return tree;
}


std::shared_ptr<Tree> SHiP::get_tree(long long hierarchy) {
    auto it = this->trees.find(hierarchy);
    if (it != this->trees.end()) {
        return it->second;
    }

    if (hierarchy == 0) {
        LOG_ERROR << "Base tree has not been constructed.";
        throw std::runtime_error("Base tree not found.");
    } else {
        auto [tree, tree_construction_runtime] = measure_runtime<std::chrono::microseconds>(
            [this, hierarchy]() {
                return std::make_shared<Tree>(this->get_tree(0)->root, this->data, this->tree_type, hierarchy, this->config);
            });
        this->tree_construction_runtime[hierarchy] = tree_construction_runtime;

        trees.emplace(hierarchy, tree);
        return tree;
    }
}


/*
 * partitioning methods implemented in `partitioning/partitioning.cpp`
 */
// std::vector<long long> SHiP::partitioning();
