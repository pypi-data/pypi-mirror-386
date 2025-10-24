#include "print_functions.hpp"

#include <pch.hpp>


void printLabels(std::vector<long long> labels) {
    std::cout << "Labels:" << std::endl;
    std::cout << "[";
    for (long long label : labels) {
        std::cout << label << ", ";
    }
    std::cout << "]" << std::endl;
}

void print_vec(std::vector<double> vec) {
    std::cout << "v: (";
    for (unsigned long long i = 0; i < vec.size(); i++) {
        std::cout << vec[i] << ", ";
    }
    std::cout << ")" << std::endl;
}




// Function to print the tree (for debugging purposes)
void printSubtree(const std::string& prefix, const std::shared_ptr<UltrametricTreeNode> tree) {
    using std::cout;
    using std::endl;
    if (tree->children.empty()) return;
    cout << prefix;
    long long n_children = tree->children.size();
    cout << (n_children > 1 ? "├────" : "");

    for (long long i = 0; i < n_children; ++i) {
        const std::shared_ptr<UltrametricTreeNode> c = tree->children[i];
        if (i < n_children - 1) {
            if (i > 0) {
                cout << prefix << "├────";
            }
            bool printStrand = n_children > 1 && !c->children.empty();
            std::string newPrefix = prefix + (printStrand ? "│\t" : "\t");

            if (c->children.empty()) {  // Leaf case
                if (c->cost != 0) {
                    std::cout << "(L" << c->id << ")[" << c->cost << "]\n";
                } else {
                    std::cout << "(L" << c->id << ")\n";
                }
            } else {
                std::cout << "(" << c->cost << " | "
                          << ")\n";
            }
            printSubtree(newPrefix, c);
        } else {
            cout << (n_children > 1 ? prefix : "") << "└────";
            if (c->children.empty()) {  // Leaf case
                if (c->cost != 0) {
                    std::cout << "(L" << c->id << ")[" << c->cost << "]\n";
                } else {
                    std::cout << "(L" << c->id << ")\n";
                }
            } else {
                std::cout << "(" << c->cost << " | "
                          << ")\n";
            }
            printSubtree(prefix + "\t", c);
        }
    }
}

/*
    Prints the tree, costs in inner nodes and id in the leaves
        - If a relaxed ultrametric also has the leaf costs in square brackets []
*/
void printTree(const std::shared_ptr<UltrametricTreeNode> tree) {
    using std::cout;
    cout << tree->cost << " | "
         << "\n";
    printSubtree("", tree);
    cout << "\n";
}


// Function to print the tree (for debugging purposes)
void printSubtree(const std::string& prefix, const std::shared_ptr<Node>& tree) {
    using std::cout;
    using std::endl;
    if (tree->children.empty()) return;
    cout << prefix;
    long long n_children = tree->children.size();
    cout << (n_children > 1 ? "├────" : "");

    for (long long i = 0; i < n_children; ++i) {
        const std::shared_ptr<Node>& c = tree->children[i];
        if (i < n_children - 1) {
            if (i > 0) {
                cout << prefix << "├────";
            }
            bool printStrand = n_children > 1 && !c->children.empty();
            std::string newPrefix = prefix + (printStrand ? "│\t" : "\t");

            if (c->children.empty()) {  // Leaf case
                if (c->cost != 0) {
                    std::cout << "(L" << c->id << ")[" << c->cost << "] | " << tree->low << " " << tree->high << "\n";
                } else {
                    std::cout << "(L" << c->id << ") | " << tree->low << " " << tree->high << "\n";
                }
            } else {
                std::cout << "(" << c->cost << " | " << c->size << ") | " << tree->low << " " << tree->high << "\n";
            }
            printSubtree(newPrefix, c);
        } else {
            cout << (n_children > 1 ? prefix : "") << "└────";
            if (c->children.empty()) {  // Leaf case
                if (c->cost != 0) {
                    std::cout << "(L" << c->id << ")[" << c->cost << " | " << tree->low << " " << tree->high << "\n";
                } else {
                    std::cout << "(L" << c->id << ") | " << tree->low << " " << tree->high << "\n";
                }
            } else {
                std::cout << "(" << c->cost << " | " << c->size << ") | " << tree->low << " " << tree->high << "\n";
            }
            printSubtree(prefix + "\t", c);
        }
    }
}

/*
    Prints the tree, costs in inner nodes and id in the leaves
        - If a relaxed ultrametric also has the leaf costs in square brackets []
*/
void printTree(const std::shared_ptr<Node>& tree) {
    using std::cout;
    cout << tree->cost << " | " << tree->size <<  " | " << tree->low << " " << tree->high << "\n";
    printSubtree("", tree);
    cout << "\n";
}


// Function to print the tree (for debugging purposes)
// This function will also show merges and splits (i.e. the nodes at which to cut) if used within kcenter.
void printSubtree_clusterMarkings(const std::string& prefix, const std::shared_ptr<Node>& tree) {
    using std::cout;
    using std::endl;
    if (tree->children.empty()) return;
    cout << prefix;
    long long n_children = tree->children.size();
    cout << (n_children > 1 ? "├────" : "");

    for (long long i = 0; i < n_children; ++i) {
        std::shared_ptr<Node>& c = tree->children[i];
        if (i < n_children - 1) {
            if (i > 0) {                    // added fix
                cout << prefix << "├────";  // added fix
            }                               // added fix
            bool printStrand = n_children > 1 && !c->children.empty();
            std::string newPrefix = prefix + (printStrand ? "│\t" : "\t");
            if (c->is_cluster) {
                if (c->is_merger) {
                    std::cout << "[ M ]";
                } else {
                    std::cout << "[ C ]";
                }
            }
            if (c->children.empty()) {
                if (c->cost != 0) {
                    std::cout << "(L" << c->id << ")[" << c->cost << "]\n";
                } else {
                    std::cout << "(L" << c->id << ")\n";
                }
            } else {
                std::cout << "(" << c->cost << ")\n";
            }
            printSubtree_clusterMarkings(newPrefix, c);
        } else {
            cout << (n_children > 1 ? prefix : "") << "└────";
            if (c->is_cluster) {
                if (c->is_merger) {
                    std::cout << "[ M ]";
                } else {
                    std::cout << "[ C ]";
                }
            }
            if (c->children.empty()) {
                if (c->cost != 0) {
                    std::cout << "(L" << c->id << ")[" << c->cost << "]\n";
                } else {
                    std::cout << "(L" << c->id << ")\n";
                }
            } else {
                std::cout << "(" << c->cost << ")\n";
            }
            printSubtree_clusterMarkings(prefix + "\t", c);
        }
    }
}

/*
    Same as printTree, but detects is_cluster and is_merger markings
*/
void printTree_clusterMarkings(const std::shared_ptr<Node>& tree) {
    using std::cout;
    cout << tree->cost << "\n";
    printSubtree_clusterMarkings("", tree);
    cout << "\n";
}




// Function to print the tree (for debugging purposes)
// This function will also show merges and splits (i.e. the nodes at which to cut) if used within kcenter.
void printSubtree_k(const std::string& prefix, const std::shared_ptr<Node>& tree) {
    using std::cout;
    using std::endl;
    if (tree->children.empty()) return;
    cout << prefix;
    long long n_children = tree->children.size();
    cout << (n_children > 1 ? "├────" : "");

    for (long long i = 0; i < n_children; ++i) {
        std::shared_ptr<Node>& c = tree->children[i];
        if (i < n_children - 1) {
            if (i > 0) {                    // added fix
                cout << prefix << "├────";  // added fix
            }                               // added fix
            bool printStrand = n_children > 1 && !c->children.empty();
            std::string newPrefix = prefix + (printStrand ? "│\t" : "\t");
            if (c->is_cluster) {
                if (c->is_merger) {
                    std::cout << "[ M ]";
                } else {
                    std::cout << "[ C ]";
                }
            }
            if (c->children.empty()) {
                if (c->cost != 0) {
                    std::cout << "(L" << c->k << ")[" << c->cost << "]\n";
                } else {
                    std::cout << "(L" << c->k << ")\n";
                }
            } else {
                std::cout << "(" << c->k << ")\n";
            }
            printSubtree_k(newPrefix, c);
        } else {
            cout << (n_children > 1 ? prefix : "") << "└────";
            if (c->is_cluster) {
                if (c->is_merger) {
                    std::cout << "[ M ]";
                } else {
                    std::cout << "[ C ]";
                }
            }
            if (c->children.empty()) {
                if (c->cost != 0) {
                    std::cout << "(L" << c->k << ")[" << c->cost << "]\n";
                } else {
                    std::cout << "(L" << c->k << ")\n";
                }
            } else {
                std::cout << "(" << c->k << ")\n";
            }
            printSubtree_k(prefix + "\t", c);
        }
    }
}


/*
    Same as printTree, but detects is_cluster and is_merger markings
*/
void printTree_k(const std::shared_ptr<Node>& tree) {
    using std::cout;
    cout << tree->cost << "\n";
    printSubtree_k("", tree);
    cout << "\n";
}



void print_annotations(std::vector<Annotation*> annotations) {
    long long i = 0;
    std::cout << "Annotations:" << std::endl;
    std::cout << "[";
    for (Annotation* anno : annotations) {
        std::cout << "i" << i;
        // std::cout << std::fixed << std::setprecision(15); // Set precision for floating-point numbers

        if (anno->parent.lock() == nullptr) {
            std::cout << "(" << anno->cost_decrease << ", " << anno->center << "), ";
        } else {
            std::cout << "(" << anno->cost_decrease << ", " << anno->center << ", " << anno->parent.lock()->center << "), ";
        }
        i++;
    }
    std::cout << "]" << std::endl;
}


std::ostream& operator<<(std::ostream& os, std::shared_ptr<Annotation>& annotation) {
    os << "Annotation: " << annotation->center << "\n ";
    os << "  Cost Decrease: " << annotation->cost_decrease << "\n";

    // Print parent (weak_ptr, may not be valid)
    if (auto parent = annotation->parent.lock()) {
        os << "  Parent Center: " << parent->center << "\n";
    } else {
        os << "  Parent: null\n";
    }

    // Print tree_node (shared_ptr)
    if (annotation->tree_node.lock()) {
        os << "  Tree Node ID: " << annotation->tree_node.lock()->id << "\n";
    } else {
        os << "  Tree Node: null\n";
    }

    // Print orig_node (weak_ptr, may not be valid)
    if (auto orig_node = annotation->orig_node.lock()) {
        os << "  Original Node ID: " << orig_node->id << "\n";
    } else {
        os << "  Original Node: null\n";
    }
    return os;
}



std::ostream& operator<<(std::ostream& os, std::shared_ptr<Node>& node) {
    os << "Node: " << node->id << "\n ";
    os << "  Cost: " << node->cost << "\n\n";
    return os;
}
