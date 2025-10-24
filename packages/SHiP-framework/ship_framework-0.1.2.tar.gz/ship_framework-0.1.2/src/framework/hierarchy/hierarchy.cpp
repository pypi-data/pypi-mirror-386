#include <framework/tree_structure.hpp>
#include <pch.hpp>


/*
    The function that creates the list of cost_decrease annotations.
    It returns a list with the length of number of leaves, as we only store maximal annotations for each center.
*/
void Tree::annotate_tree(std::shared_ptr<Node> root, std::vector<std::vector<double>>& data) {
    this->max_cost = (double)root->size * this->cost_function(root->cost);
    this->k_solutions = std::vector<std::shared_ptr<Annotation>>(root->size);

    struct Frame {
        std::shared_ptr<Node> node;
        bool childrenProcessed;  // Indicate whether the "recursive call" is on its way up or down
        long long level;         // Avoid doing computations more than necessarily, also helsp in the edge case of the root being the best cluster (which we do not allow)

        Frame(std::shared_ptr<Node> node, bool childrenProcessed, long long level)
            : node(std::move(node)), childrenProcessed(childrenProcessed), level(level) {}
    };
    std::vector<Frame> callStack;
    std::vector<std::pair<double, long long>> returnStack;

    callStack.emplace_back(root, false, 0);
    while (!callStack.empty()) {
        Frame& frame = callStack.back();
        std::shared_ptr<Node> node = frame.node;
        long long level = frame.level;

        if (!frame.childrenProcessed) {
            frame.childrenProcessed = true;
            node->level = level;
            for (std::shared_ptr<Node> child : node->children) {
                callStack.emplace_back(child, false, level + 1);
            }

            if (node->children.empty()) {
                auto parent = node->parent.lock();
                double parent_cost = parent ? this->cost_function(parent->cost) : this->cost_function(node->cost);
                double center_cost = this->cost_function(node->cost);
                double diff_cost = parent_cost - center_cost;

                std::shared_ptr<Annotation> annotation = std::make_shared<Annotation>(diff_cost, node->id);

                this->k_solutions[node->id] = annotation;
                annotation->orig_node = node;  // New for better tree construction
                node->anno = annotation;       // New for better tree construction

                returnStack.emplace_back(center_cost, node->id);
                callStack.pop_back();
            }
        } else {
            std::shared_ptr<Node> parent = node->parent.lock();
            double parent_cost = parent ? this->cost_function(parent->cost) : this->cost_function(node->cost);
            double node_cost = this->cost_function(node->cost);

            double best_cost = std::numeric_limits<double>::infinity();
            long long best_center = -1;
            std::vector<long long> centers;
            for (std::shared_ptr<Node> child : node->children) {
                // Run through the children of the current node and find the lowest
                auto [child_cost, child_id] = returnStack.back();
                returnStack.pop_back();

                double curr_cost = node_cost * (double)(node->size - child->size) + child_cost;

                if (curr_cost <= best_cost) {
                    best_cost = curr_cost;
                    best_center = child_id;
                }
                centers.push_back(child_id);
            }
            // For parent node the cost decrease is just the cost of k=1 solution
            double cost_decrease = parent_cost * (double)node->size - best_cost;
            // Update annotation list
            for (const long long center : centers) {
                if (center == best_center) {
                    continue;
                }
                this->k_solutions[center]->parent = this->k_solutions[best_center];
            }
            this->k_solutions[best_center]->cost_decrease = cost_decrease;
            this->k_solutions[best_center]->level = level;

            node->anno = this->k_solutions[best_center];
            returnStack.emplace_back(best_cost, best_center);
            callStack.pop_back();
        }
    }

    std::sort(this->k_solutions.begin(), this->k_solutions.end(), [](const std::shared_ptr<Annotation>& a, const std::shared_ptr<Annotation>& b) {
        return *a > *b;
    });

    // Only apply heuristic if it is not the base tree
    if (this->hierarchy != 0) {
        // Create the tree with heuristics based placement of equidistant branches. This is why we need the dataset here.
        std::vector<std::string> keys = {"tiebreaker_method", "tiebreaker"};
        std::vector<std::string> euclidean_aliases = {"euclidean_distance", "euclidean_dist", "euclidean"};
        std::string tiebreaker_method = get_config_value(this->config, keys, euclidean_aliases[0]);
        if (tiebreaker_method == "random") {
            // Do nothing.
        } else if (check_key_occurs(tiebreaker_method, euclidean_aliases)) {
            optimize_annotations(root, data);
        } else {
            LOG_WARN << "Invalid value for '" << keys[0] << "': '" << tiebreaker_method
                     << "'. Using default: '" << euclidean_aliases[0] << "'";
            optimize_annotations(root, data);
        }
    }

    this->cost_decreases.clear();
    this->cost_decreases.reserve(this->k_solutions.size());
    for (std::shared_ptr<Annotation> anno : this->k_solutions) {
        this->cost_decreases.push_back(anno->cost_decrease);
    }
}


/*
    Main workhorse function that creates the tree itself from the annotations.
    It also annotates each node in the tree with the k value that created it.
    This ensures it is easy to get out k solutions efficiently afterwards.
    Internal nodes end up having id of the center / cluster that its leaves will be part of.
*/
std::shared_ptr<Node> Tree::create_centroids_hierarchy() {
    std::shared_ptr<Node> root_pointer = std::make_shared<Node>(this->k_solutions[0]->center, 0.0);
    root_pointer->k = 1;
    this->k_solutions[0]->tree_node = root_pointer;

    for (unsigned long long i = 1; i < this->k_solutions.size(); i++) {
        std::shared_ptr<Annotation> curr_anno = this->k_solutions[i];
        std::shared_ptr<Node> new_node = std::make_shared<Node>(curr_anno->center, 0.0);
        new_node->k = i + 1;
        curr_anno->tree_node = new_node;
        std::shared_ptr<Annotation> parent_anno = curr_anno->parent.lock();
        std::shared_ptr<Node> parent_node = parent_anno->tree_node.lock();
        double cost = parent_node->cost;
        if (cost != curr_anno->cost_decrease && parent_node->children.size() > 0) {
            // No more new nodes added to current parent, update the pointers
            std::shared_ptr<Node> new_parent = parent_node->children[0];
            // parent, cost, id, k. We know the splitter is always the first entry.
            new_node->parent = new_parent;
            // we are done with the previous parent node that annotation pointed to
            parent_anno->tree_node = new_parent;
            new_parent->cost = curr_anno->cost_decrease;

            std::shared_ptr<Node> new_splitter = std::make_shared<Node>(new_parent->id, 0.0, std::vector<std::shared_ptr<Node>>(), new_parent, i + 1);
            new_splitter->parent = new_parent;

            new_parent->children.push_back(new_splitter);
            new_parent->children.push_back(new_node);
        } else if (parent_node->children.empty()) {
            // csize is 0 here [First child added to empty parent, add two nodes to parent]
            std::shared_ptr<Node> new_splitter = std::make_shared<Node>(parent_node->id, 0.0, std::vector<std::shared_ptr<Node>>(), parent_node, i + 1);  // parent, cost, id, k
            parent_node->cost = curr_anno->cost_decrease;
            new_node->parent = parent_node;

            parent_node->children.push_back(new_splitter);
            parent_node->children.push_back(new_node);
        } else {
            // Cost_decrease == parent cost_decrease
            parent_node->children.push_back(new_node);
            new_node->parent = parent_node;
        }
    }
    return root_pointer;
}



//################################ OPT TREE COMP ###################################


/*
    Computes the mean representative point for each node in the tree bottom up.
    Also "resets" k_markings and closest center values.
*/
void Tree::compute_representatives(std::shared_ptr<Node> root,
                                   std::vector<std::vector<double>>& data) {
    const size_t dim = data[0].size();
    std::vector<double> new_representative(dim);

    std::vector<std::pair<std::shared_ptr<Node>, bool>> stack;
    stack.reserve(sorted_nodes.size() * 2);
    stack.emplace_back(root, false);

    while (!stack.empty()) {
        auto [node, children_done] = stack.back();
        stack.pop_back();

        // Reset per-node state
        node->k_marking = -1;
        node->closest_center = std::numeric_limits<double>::infinity();

        if (node->children.empty()) {
            // Leaf: representative is the original data point
            node->representative = data[node->id];
        } else {
            if (!children_done) {
                // Push node back for post-order processing
                stack.emplace_back(node, true);
                // Then push children
                for (auto& child : node->children) {
                    stack.emplace_back(child, false);
                }
            } else {
                // Post-order: combine child representatives into 'new_representative'
                std::fill(new_representative.begin(), new_representative.end(), 0.0);

                // Sum weight-scaled child reps
                for (auto& child : node->children) {
                    const auto& cluster_representative = child->representative;
                    double size = static_cast<double>(child->size);
                    // Pointer iteration is even faster:
                    for (size_t i = 0; i < dim; ++i) {
                        new_representative[i] += cluster_representative[i] * size;
                    }
                }

                // Normalize by this node’s size
                double inv_size = 1.0 / static_cast<double>(node->size);
                for (size_t i = 0; i < dim; ++i) {
                    new_representative[i] *= inv_size;
                }

                // Move the result into the node (avoid an extra copy)
                node->representative = std::move(new_representative);
                // Restore new_representative size for reuse
                new_representative.assign(dim, 0.0);
            }
        }
    }
}


inline double Tree::sq_euclid_dist(std::vector<double>& p1, std::vector<double>& p2) {
    long long dim = p1.size();
    double total = 0;
    for (long long i = 0; i < dim; i++) {
        double diff = p1[i] - p2[i];
        total += diff * diff;
    }
    return total;
}


/*
    Goes from the given start node and moves to the root, and checks if its representative is closer to equidistant points than current best equidistant point.
*/
void Tree::update_pointers(std::vector<double>& center, std::shared_ptr<Annotation> curr_anno, std::shared_ptr<Node> start_node, long long k) {
    // Mark the start node immediately
    start_node->k_marking = k;

    // Cache the cost_decrease of the current annotation once
    const double curr_cost_dec = curr_anno->cost_decrease;

    // Traverse up the tree via raw pointers rather than repeated weak_ptr.lock()
    Node* node = start_node->parent.lock().get();
    while (node) {
        // Mark this node if not already done
        if (node->k_marking == -1) {
            node->k_marking = k;
        }

        for (auto& child_ptr : node->children) {
            Node* child = child_ptr.get();

            if (child->k_marking != -1)
                continue;  // skip already‐marked subtrees

            // ensure that we with triplets do not make weird double nodes
            if (child->anno->cost_decrease != curr_cost_dec) {
                // Compute squared Euclidean distance
                double dist = sq_euclid_dist(center, child->representative);

                // Update if this center is closer
                if (dist < child->closest_center) {
                    child->closest_center = dist;
                    child->anno->parent = curr_anno;
                }
            }
        }

        // Move up once more
        node = node->parent.lock().get();
    }
}

/*
    Gets as input the sorted list of annotations.
    It computes bottom up the center markings - if a child of its path is unmarked (could have been marked by another previous center),
    then update that annotation to point to this if the distance is smaller than the one currently for the one it is pointing to.
    It might just reupdate to the original one, but this is negligible overhead from not having an arbitrary line of code checking this.
*/
void Tree::optimize_annotations(std::shared_ptr<Node> root, std::vector<std::vector<double>>& data) {
    compute_representatives(root, data);
    for (unsigned long long i = 0; i < this->k_solutions.size(); i++) {
        std::shared_ptr<Annotation> curr_anno = this->k_solutions[i];
        std::vector<double>& curr_center_point = data[curr_anno->center];
        std::shared_ptr<Node> curr_node = curr_anno->orig_node.lock();
        update_pointers(curr_center_point, curr_anno, curr_node, i);
    }
}
