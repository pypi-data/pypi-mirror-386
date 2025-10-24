#include "available_trees.hpp"

#include <pch.hpp>


// From UltrametricTreeType to string
std::string ultrametric_tree_type_to_string(UltrametricTreeType type) {
    for (const auto& [key, value] : ultrametricTreeTypeStrings) {
        if (key == type) return std::string(value);
    }
    LOG_ERROR << "Selected UltrametricTreeType is invalid!";
    throw std::invalid_argument("Invalid UltrametricTreeType");
}

// From string to UltrametricTreeType
UltrametricTreeType string_to_ultrametric_tree_type(const std::string& type) {
    for (const auto& [key, value] : ultrametricTreeTypeStrings) {
        if (to_lower(std::string(value)) == to_lower(type)) return key;
    }
    LOG_ERROR << "Selected UltrametricTreeType string '" << type << "' is invalid!";
    throw std::invalid_argument("Invalid UltrametricTreeType string");
}

// Get all available UltrametricTreeTypes
std::vector<UltrametricTreeType> get_available_ultrametric_tree_types() {
    std::vector<UltrametricTreeType> result;
    result.reserve(ultrametricTreeTypeStrings.size());
    for (const auto& [type, name] : ultrametricTreeTypeStrings) {
        result.emplace_back(type);
    }
    return result;
}

// Get all available UltrametricTreeTypes as strings
std::vector<std::string> get_available_ultrametric_tree_types_as_strings() {
    std::vector<std::string> result;
    result.reserve(ultrametricTreeTypeStrings.size());
    for (const auto& [type, name] : ultrametricTreeTypeStrings) {
        result.emplace_back(name);
    }
    return result;
}
