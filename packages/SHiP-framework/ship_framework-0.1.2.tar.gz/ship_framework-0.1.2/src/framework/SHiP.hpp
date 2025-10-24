#pragma once

#include <framework/partitioning/available_partitionings.hpp>
#include <framework/tree_construction/available_trees.hpp>
#include <framework/tree_structure.hpp>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>


const UltrametricTreeType DEFAULT_ULTRAMETRIC_TREE_TYPE = UltrametricTreeType::DCTree;
const std::string DEFAULT_ULTRAMETRIC_TREE_TYPE_STRING = ultrametric_tree_type_to_string(DEFAULT_ULTRAMETRIC_TREE_TYPE);
const long long DEFAULT_HIERARCHY = 1;
const PartitioningMethod DEFAULT_PARTITIONING_METHOD = PartitioningMethod::MedianOfElbows;
const std::string DEFAULT_PARTITIONING_METHOD_STRING = partitioning_method_to_string(DEFAULT_PARTITIONING_METHOD);
const std::unordered_map<std::string, std::string> DEFAULT_CONFIG = {};



class SHiP {
private:
    std::vector<std::vector<double>> data;
    std::unordered_map<long long, std::shared_ptr<Tree>> trees;

public:
    UltrametricTreeType tree_type;
    long long hierarchy;
    PartitioningMethod partitioning_method;

    std::unordered_map<std::string, std::string> config;

    // Cluster Labels
    std::vector<long long> labels_;

    // Runtimes
    long long partitioning_runtime = 0;
    std::unordered_map<long long, long long> tree_construction_runtime;


    // Constructors
    SHiP(std::vector<std::vector<double>>& data,
         UltrametricTreeType tree_type = DEFAULT_ULTRAMETRIC_TREE_TYPE,
         long long hierarchy = DEFAULT_HIERARCHY,
         PartitioningMethod partitioning_method = DEFAULT_PARTITIONING_METHOD,
         const std::unordered_map<std::string, std::string>& config = DEFAULT_CONFIG);


    // Methods
    void fit(std::optional<long long> hierarchy = std::nullopt, std::optional<PartitioningMethod> partitioning_method = std::nullopt, const std::unordered_map<std::string, std::string>& config = {});

    std::vector<long long> fit_predict(std::optional<long long> hierarchy = std::nullopt, std::optional<PartitioningMethod> partitioning_method = std::nullopt, const std::unordered_map<std::string, std::string>& config = {});

    std::shared_ptr<Tree> get_tree(long long hierarchy = 0);


private:
    std::vector<long long> partitioning();

    std::shared_ptr<Tree> construct_base_tree(std::vector<std::vector<double>>& data);
};
