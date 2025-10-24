#include "tree_partitioning.hpp"

#include <framework/partitioning/elbow_methods.hpp>
#include <framework/tree_structure.hpp>
#include <pch.hpp>



/*
    This method labels clusters based on the is_cluster field of the internal nodes of a tree.
    It bases the labelling on the first "true" encountered top down and ignores those further down.

*/
std::vector<long long> label_clusters(std::shared_ptr<Node> tree) {
    long long n = tree->size;
    std::vector<long long> labels(n);

    long long ctr = -1;
    std::vector<std::pair<std::shared_ptr<Node>, bool>> stack;
    stack.emplace_back(tree, false);

    while (!stack.empty()) {
        auto [curr_node, within_cluster] = stack.back();
        stack.pop_back();
        if (curr_node->children.empty()) {  // leaf
            // This is not a cluster node itself, however it might be contained in a cluster
            if (within_cluster) {
                labels[curr_node->id] = ctr;
            } else {
                if (curr_node->is_cluster) {  // In the case that mcs = 1 and this actually becomes a cluster (if no clusters seen higher up in recursion)
                    ctr++;
                    labels[curr_node->id] = ctr;
                } else {
                    labels[curr_node->id] = -1;
                }
            }
        } else {  //
            if (!within_cluster && curr_node->is_cluster) {
                within_cluster = true;
                ctr++;
            }
            for (std::shared_ptr<Node> child : curr_node->children) {  // Recurse and update the ctr as we go so that we ensure each cluster gets unique id.
                stack.emplace_back(child, within_cluster);
            }
        }
    }

    return labels;
}


/*
    For get_k_solution we always start from the top of the tree and do it top down instead of from a potential previous solution.
    It works by taking the nodes above the cut of any nodes with annotated k values > k.
*/
std::vector<long long> Tree::kcenter_cut(long long k) {
    return k_solution(k, this->root);
}

std::vector<long long> Tree::kcenter_elbow_cut(bool triangle) {
    return k_solution(get_elbow_k(triangle), this->root);
}

std::vector<long long> Tree::threshold_elbow_cut() {
    long long k = threshold();
    return label_clusters_merge(this->root, k);
}

std::vector<long long> Tree::threshold_cut(long long k) {
    k = threshold(k);
    return label_clusters_merge(this->root, k);
}

std::vector<long long> Tree::stability_cut(unsigned long long mcs) {
    bottom_up_cluster(this->root, mcs);
    return label_clusters_merge(this->root);
}

std::vector<long long> Tree::normalized_stability_cut(unsigned long long mcs) {
    bottom_up_cluster_normalized(this->root, mcs);
    return label_clusters_merge(this->root);
}


std::vector<long long> Tree::threshold_q_coverage(long long k, unsigned long long minPts, bool prune_stem, bool elbow, bool use_full_tree_elbow) {
    std::vector<std::shared_ptr<Node>> full_tree_sorted = this->sorted_nodes;  // Save the old sorted list to reinstate it after pruned tree computations
    this->sorted_nodes = prune_tree_fast(full_tree_sorted, minPts);

    if (elbow) {
        if (!use_full_tree_elbow) {
            std::vector<double> costs_list;
            for (std::shared_ptr<Node> node : this->sorted_nodes) {
                if (node->cost != 0) {
                    costs_list.push_back(node->cost);
                }
            }
            std::vector<double> full_costs = this->costs;
            this->costs = costs_list;
            k = threshold(0, prune_stem, true);
            this->costs = full_costs;
        } else {
            k = threshold(0, prune_stem, true);
        }
    } else {
        k = threshold(k, prune_stem, true);
    }
    mark_tree_from_pruned(this->sorted_nodes);
    this->sorted_nodes = full_tree_sorted;  // Restore to original set of sorted nodes
    return label_clusters_merge(this->root, k);
}


std::vector<long long> Tree::get_lca_prune_solution(bool triangle) {
    unsigned long long k = 0;
    if (triangle) {
        k = elbow_triangle(this->costs);  // This currently uses the triangle method
    } else {
        k = elbow_line_dist(this->costs);  // This is the "old" linedist method
    }
    std::set<long long> ids;
    for (unsigned long long i = 0; i < k; i++) {
        ids.insert(this->k_solutions[i]->center);
    }
    mark_tree(this->root, ids);
    std::vector<long long> res = label_clusters(this->root);
    clean_tree(this->root);
    return res;
}


/*
    Takes the solution structure which currently consists of pruned tree nodes and substitutes the pruned nodes with orig nodes.
*/
std::shared_ptr<Node> Tree::convert_to_real_nodes_solution(std::shared_ptr<Node> pruned_solution) {
    if (pruned_solution->k == -1) {
        std::shared_ptr<Node> solution_holder = std::make_shared<Node>(-1, 0.0);
        solution_holder->k = -1;

        for (std::shared_ptr<Node> child : pruned_solution->children) {
            solution_holder->children.push_back(convert_to_real_nodes_solution(child));
        }
        return solution_holder;
    } else {
        return pruned_solution->orig_node;
    }
}


/*
    Used for LCA prune solution
*/
long long Tree::mark_tree(std::shared_ptr<Node> tree, std::set<long long> centers) {
    if (tree->size == 1) {
        if (centers.find(tree->id) != centers.end()) {
            tree->is_cluster = true;
            return 1;
        } else {
            return 0;
        }
    } else {
        long long sum = 0;
        for (std::shared_ptr<Node> child : tree->children) {
            sum += mark_tree(child, centers);
        }
        if (sum == 1) {
            tree->is_cluster = true;
        }
        return sum;
    }
}


/*
    Main work function for getting a specific k solution over the tree.
    Updates the current internal solution, which is a at most 2 deep, flat, tree structure with "fake" nodes pointing to the real nodes of the k solution.
    Can take as input either the full tree or a lower k solution.
*/
std::vector<long long> Tree::k_solution(long long k, std::shared_ptr<Node> curr_solution) {
    long long n = this->root->size;
    if (k >= n) {            // If k >= n all points should just be output
        return index_order;  // Just return each id as a unique point as default for any invalid parameter for now.
    } else if (k <= 1) {
        return std::vector<long long>(n);
    } else {
        std::shared_ptr<Node> solution_holder(std::make_shared<Node>(-1, 0.0));
        solution_holder->k = -1;  // This has a default k value that should never be part of a solution

        get_k_solution_helper(k, curr_solution, solution_holder);  // Constructs the solution
        std::vector<long long> res(n, -1);
        extract_labels(res, solution_holder);  // Extract labels from solution into res

        return res;
    }
}

/*
    The generated tree structure will never be more than two deep.
    It checks for edges crossing between lower and higher k than the search k and returns the nodes above the cut.
    Edge case is when you have multiple children, some lower and some higher than search k. Then we merge to original node those that are higher.
    Original node is the one corresponding to the center cluster that all other children took from.
*/
void Tree::get_k_solution_helper(long long k, std::shared_ptr<Node> fullTree, std::shared_ptr<Node> new_solution) {
    std::vector<std::shared_ptr<Node>> stack;
    stack.push_back(fullTree);
    while (!stack.empty()) {
        std::shared_ptr<Node> tree = stack.back();
        stack.pop_back();

        if (tree->size == 1) {
            new_solution->children.push_back(tree);  // We might end up with leaves part of the solution.
        }
        long long min_child_k = std::numeric_limits<long long>::max();
        long long max_child_k = tree->k;
        for (std::shared_ptr<Node> child : tree->children) {
            if (max_child_k < child->k) {
                max_child_k = child->k;
            }
            if (child->k < min_child_k) {
                min_child_k = child->k;
            }
        }

        if (max_child_k <= k) {  // Recurse if no cut detected
            for (auto it = tree->children.rbegin(); it != tree->children.rend(); ++it) {
                stack.push_back(*it);
            }
        } else {
            if (min_child_k > k) {  // Simple cut
                new_solution->children.push_back(tree);

            } else {  // If some children have larger k and some have smaller, we need to merge things.
                // First create the merge node:
                std::shared_ptr<Node> merge_node = std::make_shared<Node>(-1, 0.0);
                merge_node->k = -1;
                merge_node->size = 0;  // Just a "flag" value
                bool first_cluster = true;
                for (std::shared_ptr<Node> child : tree->children) {
                    if (first_cluster || child->k > k) {  // With current constructions of k markings, first cluster will always have child->k < k, so we arbitrarily use this as the node to merge to
                        merge_node->children.push_back(child);
                        first_cluster = false;
                    } else {
                        new_solution->children.push_back(child);
                    }
                }
                new_solution->children.push_back(merge_node);
            }
        }
    }
}

/*
    Helper function that labels all nodes in a tree with given label using quick pointers.
*/
void Tree::label_tree(std::vector<long long>& res, std::shared_ptr<Node> tree, long long label) {
    for (long long i = tree->low; i <= tree->high; i++) {
        long long id = this->index_order[i];
        res[id] = label;
    }
}

/*
    This function takes the solution container (which is a "pseudo" node) and loops through its children of real solution nodes
    to output the cluster labels.
*/
void Tree::extract_labels(std::vector<long long>& res, std::shared_ptr<Node> solution) {
    long long label = 0;
    for (std::shared_ptr<Node> child : solution->children) {
        if (child->size != 0) {
            label_tree(res, child, label);
        } else {
            for (std::shared_ptr<Node> child2 : child->children) {
                label_tree(res, child2, label);
            }
        }
        label++;
    }
}


// ########################## THRESHOLD CUTS ##############################

/*
    This labels based on the highest node that is a cluster. The bottom_up_cluster algorithm labels all clusters that win as true bottom up.
    *THIS CAN ALSO BE USED WHEN NO IS_MERGER IS PRESENT, i.e. for HDBSCAN*
*/
void Tree::label_clusters_helper_merge(std::shared_ptr<Node> tree, std::vector<long long>& labels, long long k) {
    long long ctr = -1;
    std::vector<std::shared_ptr<Node>> stack;
    stack.push_back(tree);
    while (!stack.empty()) {
        std::shared_ptr<Node> curr_tree = stack.back();
        stack.pop_back();
        if (curr_tree->is_merger) {
            label_tree(labels, curr_tree, k - 1);
        } else if (curr_tree->is_cluster) {
            ctr++;
            label_tree(labels, curr_tree, ctr);
        } else if (curr_tree->children.size() != 0) {
            for (auto it = curr_tree->children.rbegin(); it != curr_tree->children.rend(); ++it) {
                stack.push_back(*it);
            }
        } else {  // leaf noise case
            labels[curr_tree->id] = -1;
        }
    }
}

std::vector<long long> Tree::label_clusters_merge(std::shared_ptr<Node> tree, long long k) {
    long long n = tree->size;
    std::vector<long long> arr;
    arr.resize(n);
    label_clusters_helper_merge(tree, arr, k);

    clean_tree(tree);
    return arr;
}




/*
    Main threshold function.
    To make it perform kcenter cut even on the relaxed ultrametric, simply don't set is_cluster to false if node->cost > 0
*/
void Tree::threshold_cut_main(std::vector<std::shared_ptr<Node>>& node_list, long long k, bool force_kcenter_cut) {
    node_list[0]->is_cluster = true;
    long long num_clusters = 1;
    for (std::shared_ptr<Node> node : node_list) {
        long long num_children = node->children.size();

        node->is_cluster = false;
        num_clusters -= 1;
        if (num_clusters + num_children > k) {  // Merging action
            for (std::shared_ptr<Node> child : node->children) {
                if (num_clusters >= k - 1) {
                    child->is_cluster = true;
                    child->is_merger = true;
                    num_clusters++;
                } else {
                    child->is_cluster = true;
                    num_clusters++;
                }
            }
        } else if (num_children == 0) {
            num_clusters++;
            node->is_cluster = true;
            if (node->cost > 0 && !force_kcenter_cut) {  // This is to comply with the relaxed ultrametric cut, where the cut can ignore leaf nodes with > 0 cost, as the cut will be below its value.
                num_clusters -= 1;
                node->is_cluster = false;
            }
        } else {  // No merging action
            for (std::shared_ptr<Node> child : node->children) {
                child->is_cluster = true;
                num_clusters++;
            }
        }
        if (num_clusters >= k) {
            break;
        }
    }
}


void Tree::trim_stem(std::vector<std::shared_ptr<Node>>& node_list) {
    for (std::shared_ptr<Node> node : node_list) {
        bool is_cluster = node->is_cluster;
        bool is_merger = node->is_merger;
        if (is_cluster) {
            node->is_cluster = false;
            node->is_merger = false;
            long long num_children = node->children.size();
            std::shared_ptr<Node> curr_node = node;
            while (num_children == 1) {
                curr_node = curr_node->children[0];
                num_children = curr_node->children.size();
            }
            curr_node->is_cluster = is_cluster;
            curr_node->is_merger = is_merger;
        }
    }
}

/*
    If provided with k = 0, this will use the elbow method to find it.
*/
long long Tree::threshold(long long k, bool stemTrim, bool force_kcenter_cut) {
    std::vector<std::shared_ptr<Node>> node_list = this->sorted_nodes;
    if (k == 0) {
        k = get_elbow_k();
    }
    threshold_cut_main(node_list, k, force_kcenter_cut);
    if (stemTrim) {
        trim_stem(node_list);
    }
    return k;
}

void Tree::mark_tree_from_pruned(std::vector<std::shared_ptr<Node>> pruned_nodes) {
    for (std::shared_ptr<Node> pruned_tree : pruned_nodes) {
        std::shared_ptr<Node> orig = pruned_tree->orig_node;
        orig->is_cluster = pruned_tree->is_cluster;
        orig->is_merger = pruned_tree->is_merger;
    }
}


double Tree::stability(long long size, double pdist, double fallout_sum) {
    return fallout_sum - (double)size / pdist;  // TODO: check conversion
}


// ################################ STABILITY HDBSCAN #####################################
// This method ensures that we do not count noise branches in the split size
long long Tree::split_size(std::shared_ptr<Node> tree, unsigned long long mcs) {
    long long size = 0;
    if (mcs != 1) {
        for (std::shared_ptr<Node> child : tree->children) {
            if (child->size >= mcs) {
                size++;
            }
        }
    } else {                                                      // We might just remove this else branch if we decide to not include mcs=1
        for (std::shared_ptr<Node> child : tree->children) {      // Remember that ids are 1-indexed
            if (child->size == 1 && child->cost == tree->cost) {  // If its a leaf and has the same cdist as pdist then it does not contribute
                continue;
            }
            size++;
        }
    }
    return size;
}


/*
Uses merge_above to only compute stability at the top of cluster regions.
*/
void Tree::bottom_up_cluster(std::shared_ptr<Node> fullTree, unsigned long long min_cluster_size) {
    struct StackFrame {
        std::shared_ptr<Node> node;
        bool childrenProcessed;  // Indicate whether the "recursive call" is on its way up or down
        bool mergeAbove;         // Avoid doing computations more than necessarily, also helsp in the edge case of the root being the best cluster (which we do not allow)

        StackFrame(std::shared_ptr<Node> node, bool childrenProcessed, bool mergeAbove)
            : node(std::move(node)), childrenProcessed(childrenProcessed), mergeAbove(mergeAbove) {}
    };

    std::vector<StackFrame> callStack;
    std::vector<std::pair<double, double>> returnStack;
    callStack.emplace_back(fullTree, false, true);
    while (!callStack.empty()) {
        StackFrame& frame = callStack.back();
        std::shared_ptr<Node> tree = frame.node;
        if (!frame.childrenProcessed) {
            if (min_cluster_size > tree->size) {
                double stability_contribution = (double)tree->size * (1.0 / tree->parent.lock()->cost);
                returnStack.emplace_back(0, stability_contribution);
                callStack.pop_back();
            } else {
                frame.childrenProcessed = true;
                long long splitSize = split_size(tree, min_cluster_size);
                for (std::shared_ptr<Node> child : tree->children) {
                    if (splitSize >= 2) {  // If we have a split the stability should be computed below
                        callStack.emplace_back(child, false, true);
                    } else {
                        callStack.emplace_back(child, false, false);
                    }
                }
            }
        } else {
            callStack.pop_back();
            double total_cluster_stability = 0.0;    // Contains sum of stabilities of best below clusters
            double total_region_contribution = 0.0;  // Contains sum of the level points fall out of the cluster region
            for (std::shared_ptr<Node> child : tree->children) {
                auto [cluster_stability, region_contribution] = returnStack.back();
                returnStack.pop_back();
                total_cluster_stability += cluster_stability;
                total_region_contribution += region_contribution;
            }
            if (tree->parent.lock() == nullptr) {
                tree->is_cluster = false;
                continue;
            }

            if (frame.mergeAbove) {
                double parent_cost = tree->parent.lock()->cost;
                double new_stability = stability(tree->size, parent_cost, total_region_contribution);
                total_region_contribution = (double)tree->size / parent_cost;
                if (new_stability >= total_cluster_stability) {
                    tree->is_cluster = true;
                    returnStack.emplace_back(new_stability, total_region_contribution);
                    continue;
                }
                tree->is_cluster = false;
                returnStack.emplace_back(total_cluster_stability, total_region_contribution);
            } else {
                tree->is_cluster = false;
                returnStack.emplace_back(total_cluster_stability, total_region_contribution);
            }
        }
    }
}

void Tree::bottom_up_cluster_normalized(std::shared_ptr<Node> fullTree, unsigned long long min_cluster_size) {
    std::vector<std::pair<std::shared_ptr<Node>, bool>> callStack;
    std::vector<double> returnStack;
    callStack.emplace_back(fullTree, false);
    while (!callStack.empty()) {
        auto [tree, childrenProcessed] = callStack.back();
        callStack.pop_back();
        if (!childrenProcessed) {
            if (min_cluster_size > tree->size) {
                tree->is_cluster = false;
                returnStack.push_back(0);
            } else {
                callStack.emplace_back(tree, true);
                for (std::shared_ptr<Node> child : tree->children) {
                    callStack.emplace_back(child, false);
                }
            }
        } else {
            double total_cluster_stability = 0.0;  // This will contain the sum of stabilities of best clusters from below
            for (std::shared_ptr<Node> child : tree->children) {
                total_cluster_stability += returnStack.back();
                returnStack.pop_back();
            }

            if (tree->parent.lock() == nullptr) {  // root node //Here we can implement allowing a singular cluster to be output if want
                tree->is_cluster = false;
                returnStack.push_back(0.0);  // Just return default values in parent - nothing left to do
                continue;
            }

            double new_stability = (double)tree->size * ((tree->parent.lock()->cost / (double)tree->parent.lock()->size) - (tree->cost / (double)tree->size));  // TODO
            if (new_stability >= total_cluster_stability) {
                tree->is_cluster = true;
                returnStack.push_back(new_stability);
                continue;
            }
            tree->is_cluster = false;  // Added this to ensure that algorithm ALWAYS sets all the values of is_cluster in the tree, to not be vulnerable with multiple runs.
            returnStack.push_back(total_cluster_stability);
        }
    }
}



std::shared_ptr<Node> prune_tree(std::shared_ptr<Node>& tree, unsigned long long minPts) {
    if (tree->size < minPts) {
        throw std::invalid_argument("Tree too small to be pruned with provided k value");
    } else {
        std::shared_ptr<Node> newcopy = std::make_shared<Node>(tree->id, tree->cost, std::vector<std::shared_ptr<Node>>(), tree->parent, tree->k);
        newcopy->size = tree->size;  // Should we do this?
        newcopy->orig_node = tree;
        newcopy->k = tree->k;
        for (std::shared_ptr<Node>& child : tree->children) {
            if (child->size >= minPts) {
                newcopy->children.push_back(prune_tree(child, minPts));
            }
        }
        return newcopy;
    }
}

/*
    Takes as input a sorted list of nodes and outputs the sorted pruned list
*/
std::vector<std::shared_ptr<Node>> prune_tree_fast(std::vector<std::shared_ptr<Node>>& nodes, unsigned long long minPts) {
    std::vector<std::shared_ptr<Node>> pruned_list;
    for (std::shared_ptr<Node>& tree : nodes) {
        if (tree->size >= minPts) {
            tree->orig_node = std::make_shared<Node>(tree->id, tree->cost, std::vector<std::shared_ptr<Node>>(), tree->parent, tree->k);
        } else {
            tree->orig_node = nullptr;
        }
    }

    for (std::shared_ptr<Node>& tree : nodes) {
        if (tree->orig_node != nullptr) {
            std::shared_ptr<Node>& newcopy = tree->orig_node;
            newcopy->size = tree->size;
            newcopy->orig_node = tree;
            for (std::shared_ptr<Node>& child : tree->children) {
                if (child->orig_node != nullptr) {
                    child->orig_node->parent = newcopy;
                    newcopy->children.push_back(child->orig_node);
                }
            }
            pruned_list.push_back(newcopy);
            tree->orig_node = nullptr;
        }
    }
    return pruned_list;
}


/////////////////////////////////// CLEANUP METHODS /////////////////////////////////////

/*
    Resets markings in the tree used for labelling the final clusterings.
    Can both be used for SHiP/HDBSCAN and center-based labellings.
*/
void clean_tree(std::shared_ptr<Node> tree) {
    std::vector<std::shared_ptr<Node>> stack;
    stack.push_back(tree);
    while (!stack.empty()) {
        std::shared_ptr<Node> curr_node = stack.back();
        stack.pop_back();
        curr_node->is_cluster = false;
        curr_node->is_merger = false;
        for (std::shared_ptr<Node> child : curr_node->children) {
            stack.push_back(child);  // Push children onto the stack
        }
    }
}
