#include "parse_json_to_tree.hpp"

#include <pch.hpp>

#include "../available_trees.hpp"
#include "../ultrametric_tree_structure.hpp"


UltrametricTree parse_json_to_tree(const std::unordered_map<std::string, std::string>& config) {
    std::string json_tree_filepath = get_config_value(config, "json_tree_filepath", std::string{});
    std::string tree_type_string = get_config_value(config, "tree_type", ultrametric_tree_type_to_string(UltrametricTreeType::LoadTree));

    UltrametricTreeType tree_type = UltrametricTreeType::LoadTree;
    try {
        tree_type = string_to_ultrametric_tree_type(tree_type_string);
    } catch (const std::exception&) {
        LOG_WARN << "Provided `tree_type` in config is invalid. Using setting tree_type to `LoadTree` instead.";
    }

    if (json_tree_filepath.empty()) {
        LOG_ERROR << "Empty 'json_tree_filepath'.";
        throw std::invalid_argument("Invalid 'json_tree_filepath'");
    }

    // Deserialize back to object
    simdjson::dom::parser parser;
    simdjson::dom::element root_element = parser.load(json_tree_filepath);

    auto deserialized_root = std::make_shared<UltrametricTreeNode>(0, 0.0);
    if (!deserialized_root->from_json(root_element)) {
        LOG_ERROR << "Failed to parse '" << json_tree_filepath << "'.";
        throw std::invalid_argument("JsonTree is invalid");
    }
    return UltrametricTree{deserialized_root, tree_type, config};
}
