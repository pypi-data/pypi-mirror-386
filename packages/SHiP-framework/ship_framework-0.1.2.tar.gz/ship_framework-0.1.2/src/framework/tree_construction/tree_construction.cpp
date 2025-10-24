#include "tree_construction.hpp"

#include <pch.hpp>

#include "adapter/DCTree_adapter.hpp"
#include "adapter/HST_adapter.hpp"
#include "adapter/mlpack_trees_adapter.hpp"
#include "adapter/parse_json_to_tree.hpp"
#include "available_trees.hpp"


// Construct an UltrametricTree given the `tree_type` string
UltrametricTree constructUltrametricTree(std::vector<std::vector<double>>& data, UltrametricTreeType tree_type, const std::unordered_map<std::string, std::string> &config) {
    switch (tree_type) {
        case UltrametricTreeType::LoadTree: {
            return parse_json_to_tree(config);
        }
        case UltrametricTreeType::DCTree: {
            return build_from_DCTree(data, config);
        }
        case UltrametricTreeType::HST: {
            return build_from_HST(data, config);
        }
        case UltrametricTreeType::KDTree:
        case UltrametricTreeType::MeanSplitKDTree:
        case UltrametricTreeType::BallTree:
        case UltrametricTreeType::MeanSplitBallTree:
        case UltrametricTreeType::RPTree:
        case UltrametricTreeType::MaxRPTree:
        case UltrametricTreeType::UBTree:
        case UltrametricTreeType::RTree:
        case UltrametricTreeType::RStarTree:
        case UltrametricTreeType::XTree:
        case UltrametricTreeType::HilbertRTree:
        case UltrametricTreeType::RPlusTree:
        case UltrametricTreeType::RPlusPlusTree:
        case UltrametricTreeType::CoverTree: {
            return build_from_MLPackTree(data, tree_type, config);
        }
        default: {
            LOG_ERROR << "Selected UltrametricTreeType '" << ultrametric_tree_type_to_string(tree_type) << "' is invalid!";
            throw std::invalid_argument("Invalid UltrametricTreeType");
        }
    }
}
