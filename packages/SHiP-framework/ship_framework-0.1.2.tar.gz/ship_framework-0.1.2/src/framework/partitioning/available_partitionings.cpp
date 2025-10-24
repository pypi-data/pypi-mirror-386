#include "available_partitionings.hpp"

#include <pch.hpp>


// From PartitioningMethod to string
std::string partitioning_method_to_string(PartitioningMethod type) {
    for (const auto& [key, value] : partitioningMethodStrings) {
        if (key == type) return std::string(value);
    }
    LOG_ERROR << "Selected PartitioningMethod is invalid!";
    throw std::invalid_argument("Invalid PartitioningMethod");
}

// From string to PartitioningMethod
PartitioningMethod string_to_partitioning_method(const std::string& type) {
    for (const auto& [key, value] : partitioningMethodStrings) {
        if (to_lower(std::string(value)) == to_lower(type)) return key;
    }
    LOG_ERROR << "Selected PartitioningMethod string '" << type << "' is invalid!";
    throw std::invalid_argument("Invalid PartitioningMethod string");
}

// Get all available PartitioningMethods
std::vector<PartitioningMethod> get_available_partitioning_methods() {
    std::vector<PartitioningMethod> result;
    result.reserve(partitioningMethodStrings.size());
    for (const auto& [type, name] : partitioningMethodStrings) {
        result.emplace_back(type);
    }
    return result;
}

// Get all available PartitioningMethods as strings
std::vector<std::string> get_available_partitioning_methods_as_strings() {
    std::vector<std::string> result;
    result.reserve(partitioningMethodStrings.size());
    for (const auto& [type, name] : partitioningMethodStrings) {
        result.emplace_back(name);
    }
    return result;
}
