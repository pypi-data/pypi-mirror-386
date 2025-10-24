#include <pch.hpp>

#include "tree_structure.hpp"


// -------------- //
// Node Functions //
// -------------- //

// Serialization and Deserialization functions
std::string Node::to_json(bool fast_index) {
    fmt::memory_buffer buffer;
    auto self = shared_from_this();

    // Stack of (node, next child index)
    std::vector<std::pair<std::shared_ptr<Node>, size_t>> stack;
    stack.reserve(64);
    stack.emplace_back(self, 0);

    while (!stack.empty()) {
        auto& [node, nextChild] = stack.back();

        if (nextChild == 0) {
            // First visit: emit opening JSON
            if (fast_index) {
                fmt::format_to(std::back_inserter(buffer),
                               R"({{"id":{},"cost":{},"low":{},"high":{},)",
                               node->id, node->cost, node->low, node->high);
            } else {
                fmt::format_to(std::back_inserter(buffer),
                               R"({{"id":{},"cost":{},)",
                               node->id, node->cost);
            }

            fmt::format_to(std::back_inserter(buffer), R"("children":[)");
        }

        if (nextChild < node->children.size()) {
            // Process next child
            if (nextChild > 0) {
                fmt::format_to(std::back_inserter(buffer), ",");
            }
            auto child = node->children[nextChild];
            ++nextChild;
            stack.emplace_back(child, 0);
        } else {
            // All children done: close this node and pop stack
            fmt::format_to(std::back_inserter(buffer), "]}}");
            stack.pop_back();
        }
    }
    return std::string(buffer.begin(), buffer.end());
}



// -------------- //
// Tree Functions //
// -------------- //

// Serialization and Deserialization functions
std::string Tree::to_json(bool fast_index) {
    fmt::memory_buffer buffer;

    // Serialize tree_type
    fmt::format_to(std::back_inserter(buffer), R"({{"tree_type":"{}",)",
                   ultrametric_tree_type_to_string(this->tree_type));

    // Serialize config map
    bool first = true;
    fmt::format_to(std::back_inserter(buffer), R"("config":{{)");
    for (auto const& [k, v] : this->config) {
        if (!first) {
            fmt::format_to(std::back_inserter(buffer), ",");
        }
        first = false;
        fmt::format_to(std::back_inserter(buffer),
                       R"("{}":"{}")",
                       k, v);
    }
    fmt::format_to(std::back_inserter(buffer), "}},");

    // Serialize index_order
    if (fast_index) {
        bool first = true;
        fmt::format_to(std::back_inserter(buffer), R"("index_order":[)");
        for (size_t i = 0; i < this->index_order.size(); ++i) {
            if (!first) {
                fmt::format_to(std::back_inserter(buffer), ",");
            }
            first = false;
            fmt::format_to(std::back_inserter(buffer), "{}", this->index_order[i]);
        }
        fmt::format_to(std::back_inserter(buffer), "],");
    }

    // Serialize root (or null)
    if (this->root) {
        fmt::format_to(std::back_inserter(buffer), R"("root":)");
        fmt::format_to(std::back_inserter(buffer), "{}", this->root->to_json(fast_index));
    } else {
        fmt::format_to(std::back_inserter(buffer), R"("root":null)");
    }

    // Closing object
    fmt::format_to(std::back_inserter(buffer), "}}");

    return std::string(buffer.begin(), buffer.end());
}
