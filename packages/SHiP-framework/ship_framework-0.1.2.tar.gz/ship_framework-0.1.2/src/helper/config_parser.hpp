#pragma once

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <unordered_map>

#include "logger.hpp"


// Helper: convert any string to a lowercase string
inline std::string to_lower(const std::string& s) {
    std::string tmp{s};
    std::transform(tmp.begin(), tmp.end(), tmp.begin(), ::tolower);
    std::erase_if(tmp, [](char c) { return c == '_' || c == '-'; });
    return tmp;
}


inline std::optional<std::string> find_normalized_key(
    const std::unordered_map<std::string, std::string>& config,
    const std::vector<std::string>& keys) {
    for (const std::string& query_key : keys) {
        const std::string norm_query = to_lower(query_key);
        for (const auto& [k, v] : config) {
            if (to_lower(k) == norm_query)
                return v;
        }
    }
    return std::nullopt;
}


// helper to trigger static_assert in unsupported branches
template <typename>
inline constexpr bool always_false_v = false;

template <typename T>
T get_config_value(const std::unordered_map<std::string, std::string>& config,
                   const std::vector<std::string>& keys,
                   T default_value,
                   bool info_msg = false) {
    std::optional<std::string> optional_value = find_normalized_key(config, keys);
    if (!optional_value) {
        if (info_msg) {
            LOG_INFO << "Value for '" << keys[0] << "' not provided. Using default: " << default_value;
        }
        return default_value;
    }

    std::string value = optional_value.value();
    try {
        if constexpr (std::is_same_v<T, int>) {
            return std::stoi(value);
        } else if constexpr (std::is_same_v<T, double>) {
            return std::stod(value);
        } else if constexpr (std::is_same_v<T, long long>) {
            return std::stoll(value);
        } else if constexpr (std::is_same_v<T, unsigned long long>) {
            return std::stoull(value);
        } else if constexpr (std::is_same_v<T, size_t>) {
            return static_cast<size_t>(std::stoull(value));
        } else if constexpr (std::is_same_v<T, std::string>) {
            return value;
        } else if constexpr (std::is_same_v<T, const char*>) {
            return value.c_str();
        } else if constexpr (std::is_same_v<T, bool>) {
            std::string lower = to_lower(value);
            if (lower == "true" || lower == "1" || lower == "yes") return true;
            if (lower == "false" || lower == "0" || lower == "no") return false;
            throw std::invalid_argument("bool");
        } else {
            static_assert(always_false_v<T>, "Unsupported type in get_config_value");
        }
    } catch (const std::exception&) {
        LOG_WARN << "Invalid value for '" << keys[0] << "': '" << value
                 << "'. Using default: " << default_value;
        return default_value;
    }
}


template <typename T>
T get_config_value(const std::unordered_map<std::string, std::string>& config,
                   const std::string& key,
                   T default_value,
                   bool info_msg = false) {
    T value = get_config_value<T>(config, std::vector<std::string>{key}, default_value, info_msg);
    return value;
}


// Helper: validate value is in range
template <typename T>
void validate_value_in_range(T value, const std::string& value_name, T max, T min = 1) {
    if (value < min || value > max) {
        LOG_ERROR << value_name << " = " << value << " must be between " << min << " and " << max << ".";
        throw std::invalid_argument(
            value_name + " = " + std::to_string(value) +
            " must be between " + std::to_string(min) + " and " +
            std::to_string(max) + ".");
    }
}


template <typename T>
T get_config_value_in_range(const std::unordered_map<std::string, std::string>& config,
                            const std::string& key,
                            T default_value,
                            T min,
                            T max,
                            bool info_msg = false) {
    T value = get_config_value<T>(config, key, default_value, info_msg);
    validate_value_in_range(value, key, max, min);
    return value;
}


inline bool check_key_occurs(std::string& key, std::vector<std::string>& values) {
    std::string normalized_key = to_lower(key);

    for (std::string& alias : values) {
        if (to_lower(alias) == normalized_key) {
            return true;
        }
    }
    return false;
}
