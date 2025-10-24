#include <pch.hpp>

#include "ultrametric_tree_structure.hpp"


// ----------------------------- //
// UltrametricTreeNode Functions //
// ----------------------------- //

// Serialization and Deserialization functions
std::string UltrametricTreeNode::to_json() {
    fmt::memory_buffer buffer;
    auto self = shared_from_this();

    // Stack of (node, next child index)
    std::vector<std::pair<std::shared_ptr<UltrametricTreeNode>, size_t>> stack;
    stack.reserve(64);
    stack.emplace_back(self, 0);

    while (!stack.empty()) {
        auto& [node, nextChild] = stack.back();

        if (nextChild == 0) {
            // First visit: emit opening JSON
            fmt::format_to(std::back_inserter(buffer),
                           R"({{"id":{},"cost":{},)",
                           node->id, node->cost);
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


bool UltrametricTreeNode::from_json(std::string& json) {
    simdjson::dom::parser parser;
    // Parse the entire document
    simdjson::dom::element root_elem;
    auto error = parser.parse(json).get(root_elem);
    if (error != simdjson::SUCCESS) {
        LOG_ERROR << "Couldn't parse 'root'." << std::endl
                  << error;
        throw std::runtime_error("Couldn't parse 'root'.\n" + std::string(simdjson::error_message(error)));
        return false;
    }
    return this->from_json(root_elem);
}

bool UltrametricTreeNode::from_json(simdjson::dom::element root_elem) {
    // You must inherit enable_shared_from_this<UltrametricTreeNode>
    auto self = shared_from_this();

    struct Frame {
        std::shared_ptr<UltrametricTreeNode> node;
        simdjson::dom::element elem;
        simdjson::dom::array child_array;
        size_t nextChild = 0;
        bool meta_parsed = false;

        Frame(
            std::shared_ptr<UltrametricTreeNode> node,
            simdjson::dom::element elem,
            simdjson::dom::array child_array,
            size_t nextChild,
            bool meta_parsed) : node(std::move(node)),
                                elem(elem),
                                child_array(child_array),
                                nextChild(nextChild),
                                meta_parsed(meta_parsed) {}
    };

    std::vector<Frame> stack;
    stack.reserve(64);
    stack.emplace_back(self, root_elem, simdjson::dom::array(), 0, false);

    while (!stack.empty()) {
        Frame& frame = stack.back();

        // 1) Parse id, cost, and extract children array exactly once
        if (!frame.meta_parsed) {
            // id
            if (auto id = frame.elem["id"].get_int64(); id.error() == simdjson::SUCCESS) {
                frame.node->id = id.value();
            } else {
                LOG_ERROR << "Couldn't parse 'id'.";
                throw std::runtime_error("Couldn't parse 'id'.");
                return false;
            }

            // cost
            if (auto cost = frame.elem["cost"].get_double(); cost.error() == simdjson::SUCCESS) {
                frame.node->cost = cost.value();
            } else {
                LOG_ERROR << "Couldn't parse 'cost'.";
                throw std::runtime_error("Couldn't parse 'cost'.");
                return false;
            }

            // children array
            if (auto arr = frame.elem["children"].get_array(); arr.error() == simdjson::SUCCESS) {
                frame.child_array = arr.value();
                frame.node->children.clear();
            } else {
                LOG_ERROR << "Couldn't parse 'children'.";
                throw std::runtime_error("Couldn't parse 'children'.");
                return false;
            }

            frame.meta_parsed = true;
        }

        // 2) Process next child, if any remain
        if (frame.nextChild < frame.child_array.size()) {
            // grab the JSON element for this child
            auto it = frame.child_array.begin();
            std::advance(it, frame.nextChild);
            simdjson::dom::element child_elem = *it;

            // create the new node and attach to parent
            auto child_node = std::make_shared<UltrametricTreeNode>(0, 0.0);
            frame.node->children.push_back(child_node);

            // increment so that when we return, we move on
            ++frame.nextChild;

            // push new frame for this child; its meta_parsed==false by default
            stack.emplace_back(child_node, child_elem, simdjson::dom::array(), 0, false);
        } else {
            // 3) All children done → pop back up
            stack.pop_back();
        }
    }

    return true;
}



// ------------------------- //
// UltrametricTree Functions //
// ------------------------- //

// Serialization and Deserialization functions
std::string UltrametricTree::to_json() {
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

    // Serialize root (or null)
    if (this->root) {
        fmt::format_to(std::back_inserter(buffer), R"("root":)");
        fmt::format_to(std::back_inserter(buffer), "{}", this->root->to_json());
    } else {
        fmt::format_to(std::back_inserter(buffer), R"("root":null)");
    }

    // Closing object
    fmt::format_to(std::back_inserter(buffer), "}}");

    return std::string(buffer.begin(), buffer.end());
}


bool UltrametricTree::from_json(std::string& json) {
    simdjson::dom::parser parser;
    // Parse the entire document
    simdjson::dom::element elem;
    auto error = parser.parse(json).get(elem);
    if (error != simdjson::SUCCESS) {
        LOG_ERROR << "Couldn't parse 'tree'." << std::endl
                  << error;
        throw std::runtime_error("Couldn't parse 'tree'.\n" + std::string(simdjson::error_message(error)));
        return false;
    }
    return this->from_json(elem);
}

bool UltrametricTree::from_json(simdjson::dom::element elem) {
    // 1) tree_type: as string → enum
    if (auto tt = elem["tree_type"].get_string(); tt.error() == simdjson::SUCCESS) {
        std::string tt_str = std::string(tt.value());
        this->tree_type = string_to_ultrametric_tree_type(tt_str);
    } else {
        LOG_ERROR << "Couldn't parse 'tree_type'.";
        throw std::runtime_error("Couldn't parse 'tree_type'.");
        return false;
    }

    // 2) config: expect object<string,string>
    if (auto cfg = elem["config"].get_object(); cfg.error() == simdjson::SUCCESS) {
        this->config.clear();
        for (auto field : cfg.value()) {
            std::string key{field.key};
            auto val_res = field.value.get_string();
            if (val_res.error() != simdjson::SUCCESS) {
                LOG_ERROR << "Couldn't parse value of key '" << key << "'.";
                throw std::runtime_error("Couldn't parse value of key '" + key + "'.");
                return false;
            }
            std::string val{val_res.value()};
            this->config.emplace(std::move(key), std::move(val));
        }
    } else {
        LOG_ERROR << "Couldn't parse config.";
        throw std::runtime_error("Couldn't parse 'config'.");
        return false;
    }

    // 3) root: null or object
    auto rootElem = elem["root"];
    if (rootElem.error() != simdjson::SUCCESS) {
        LOG_ERROR << "Couldn't parse 'root'.";
        throw std::runtime_error("Couldn't parse 'root'.");
        return false;
    }

    if (rootElem.is_null()) {
        this->root.reset();
    } else {
        auto node = std::make_shared<UltrametricTreeNode>(0, 0.0);

        simdjson::dom::element element;
        auto error = rootElem.get(element);
        if (error) {
            LOG_ERROR << "Couldn't parse 'root'." << std::endl
                      << error;
            throw std::runtime_error("Couldn't parse 'root'.\n" + std::string(simdjson::error_message(error)));
            return false;
        }

        if (!node->from_json(element)) {
            LOG_ERROR << "Couldn't parse 'root'.";
            throw std::runtime_error("Couldn't parse 'root'.");
            return false;
        }
        this->root = std::move(node);
    }

    return true;
}
