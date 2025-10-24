#pragma once

#include <fmt/core.h>

#include <framework/tree_construction/available_trees.hpp>
#include <framework/tree_construction/ultrametric_tree_structure.hpp>
#include <memory>
#include <set>
#include <unordered_map>
#include <vector>


struct Node;  // Forward declaration for circular dependencies


struct Annotation {
    double cost_decrease;
    long long center;
    std::weak_ptr<Annotation> parent;
    std::weak_ptr<Node> tree_node;
    std::weak_ptr<Node> orig_node;  // Points to the leaf corresponding to the center
    long long level;                // Tiebreaker when ordering equal values

    Annotation(
        double cost_decrease,
        long long center,
        std::weak_ptr<Annotation> parent = std::weak_ptr<Annotation>(),
        std::weak_ptr<Node> tree_node = std::weak_ptr<Node>(),
        std::weak_ptr<Node> orig_node = std::weak_ptr<Node>(),
        long long level = 0)
        : cost_decrease(cost_decrease),
          center(center),
          parent(parent),
          tree_node(tree_node),
          orig_node(orig_node),
          level(level) {}


    bool operator<(const Annotation& other) const {
        if (cost_decrease == other.cost_decrease) {
            return level > other.level;  // Use level as the tiebreaker
        }
        return cost_decrease < other.cost_decrease;
    }

    bool operator>(const Annotation& other) const {
        if (cost_decrease == other.cost_decrease) {
            return level < other.level;  // Use level as the tiebreaker
        }
        return cost_decrease > other.cost_decrease;
    }
};
std::ostream& operator<<(std::ostream&, std::shared_ptr<Annotation>& annotation);


struct Node : std::enable_shared_from_this<Node> {
    long long id;
    double cost;
    std::vector<std::shared_ptr<Node>> children;

    std::weak_ptr<Node> parent = std::weak_ptr<Node>();
    long long k;
    unsigned long long size;

    bool is_cluster = false;  // Used to extract clusters. Used by HDBSCAN, SHiP and KCentroids.

    // Structure for quick access
    long long low;   // Fast array indexing low index
    long long high;  // Fast array indexing high index


    std::shared_ptr<Node> orig_node;
    std::shared_ptr<Annotation> anno;
    // Kcentroids annotations
    bool is_merger = false;                                           // Used for kcenter cut in a simple form
    std::vector<double> representative;                               // The point that represents that subtree. For K-centroids
    long long k_marking = -1;                                         // Used for optimizing the tree structure
    double closest_center = std::numeric_limits<double>::infinity();  // Used to check whether new center is closer or not.
    long long level;                                                  // To ensure proper ordering in the sorted list of elements


    Node(long long id,
         double cost,
         std::vector<std::shared_ptr<Node>> children = {},
         std::weak_ptr<Node> parent = std::weak_ptr<Node>(),
         long long k = -1,
         unsigned long long size = 0,
         bool is_cluster = false,
         long long low = -1,
         long long high = -1,
         std::shared_ptr<Annotation> anno = nullptr)
        : id(id), cost(cost), children(children), parent(parent), k(k), size(size), is_cluster(is_cluster), low(low), high(high), anno(anno){};

    bool operator<(const Node& other) const {
        if (cost == other.cost) {
            return level > other.level;  // Use level as the tiebreaker
        }
        return cost < other.cost;
    }

    bool operator>(const Node& other) const {
        if (cost == other.cost) {
            return level < other.level;  // Use level as the tiebreaker
        }
        return cost > other.cost;
    }

    std::string to_json(bool fast_index = false);
};
std::ostream& operator<<(std::ostream&, std::shared_ptr<Node>& node);



class Tree {
public:
    std::shared_ptr<Node> root;
    UltrametricTreeType tree_type;
    long long hierarchy;
    std::unordered_map<std::string, std::string> config;

    // Indexes for smart access
    std::vector<long long> index_order;

    std::vector<std::shared_ptr<Node>> sorted_nodes;
    std::vector<std::shared_ptr<Annotation>> k_solutions;
    double max_cost;
    std::vector<double> costs;           // For elbow method. These are sorted already.
    std::vector<double> cost_decreases;  // For elbow method. These are sorted already.


public:
    /*
        Main workhorse function that creates the tree itself from the annotations.
        It also annotates each node in the tree with the k value that created it.
        This ensures it is easy to get out k solutions efficiently afterwards.
        Internal nodes end up having id of the center / cluster that its leaves will be part of.
    */
    Tree(std::shared_ptr<Node> root, std::vector<std::vector<double>>& data, UltrametricTreeType tree_type, long long hierarchy, const std::unordered_map<std::string, std::string>& config = {});

    double cost_function(double value) {
        if (this->hierarchy <= 1) {
            return value;
        } else {
            return std::pow(value, this->hierarchy);
        }
    }

    std::vector<std::vector<double>> get_distance_matrix();

    std::string to_json(bool fast_index = false);


    /*
        For get_k_solution we always start from the top of the tree and do it top down instead of from a potential previous solution.
        It works by taking the nodes above the cut of any nodes with annotated k values > k.
    */
    std::vector<long long> kcenter_cut(long long k);

    std::vector<long long> kcenter_elbow_cut(bool triangle = true);
    std::vector<long long> threshold_elbow_cut();
    std::vector<long long> threshold_cut(long long k);

    std::vector<long long> stability_cut(unsigned long long mcs);
    std::vector<long long> normalized_stability_cut(unsigned long long mcs);

    std::vector<long long> threshold_q_coverage(long long k, unsigned long long minPts, bool prune_stem = false, bool elbow = false, bool use_full_tree_elbow = false);

    std::vector<long long> get_lca_prune_solution(bool triangle = true);


private:
    /*
        Function that adds creates an array where each leaf id is inserted in postfix order (left to right visually).
        This means each internal node has a continuous area of that array for its children, and it gets low, high pointers to its segment of the array.
        Also assigns sizes to each internal node, i.e. how many leaves does it have.
    */
    void setup_fast_index();

    /*
        Makes a list of the nodes and of the costs. Nodes used for computing the cut, and costs for the elbow.
        Also adds the level for each node to ensure correct ordering for ties.
     */
    void compute_sorted_nodes();

    void compute_sorted_costs();

    /*
        Takes as input the sorted list of nodes
    */
    void assign_nodes_their_k_values();


    /*
        Main workhorse function that creates the tree itself from the annotations.
        It also annotates each node in the tree with the k value that created it.
        This ensures it is easy to get out k solutions efficiently afterwards.
        Internal nodes end up having id of the center / cluster that its leaves will be part of.

    */
    std::shared_ptr<Node> create_centroids_hierarchy();


    /*
        The function that creates the list of cost_decrease annotations.
        It returns a list the length of number of leaves, as we only store maximal annotations for each center.
    */
    void annotate_tree(std::shared_ptr<Node> root, std::vector<std::vector<double>>& data);



    //################################ OPT TREE COMP ###################################


    double sq_euclid_dist(std::vector<double>& p1, std::vector<double>& p2);


    /*
        Goes from the given start node and moves to the root, and checks if its representative is closer to equidistant points than current best equidistant point.
    */
    void update_pointers(std::vector<double>& center, std::shared_ptr<Annotation> curr_anno, std::shared_ptr<Node> start_node, long long k);

    /*
        Gets as input the sorted list of annotations.
        It computes bottom up the center markings - if a child of its path is unmarked (could have been marked by another previous center),
        then update that annotation to point to this if the distance is smaller than the one currently for the one it is pointing to.
        It might just reupdate to the original one, but this is negligible overhead from not having an arbitrary line of code checking this.
    */
    void optimize_annotations(std::shared_ptr<Node> root, std::vector<std::vector<double>>& data);


    /*
        Computes the mean representative point for each node in the tree bottom up.
        Also "resets" k_markings and closest center values.
    */
    void compute_representatives(std::shared_ptr<Node> fullTree, std::vector<std::vector<double>>& data);



    //################################ PARTITIONING METHODS ###################################
    /*
        Takes the solution structure which currently consists of pruned tree nodes and substitutes the pruned nodes with orig nodes.
    */
    std::shared_ptr<Node> convert_to_real_nodes_solution(std::shared_ptr<Node> pruned_solution);


    /*
        Used for LCA prune solution
    */
    long long mark_tree(std::shared_ptr<Node> tree, std::set<long long> centers);


    /*
        Main work function for getting a specific k solution over the tree.
        Updates the current internal solution, which is a at most 2 deep, flat, tree structure with "fake" nodes pointing to the real nodes of the k solution.
        Can take as input either the full tree or a lower k solution.
    */
    std::vector<long long> k_solution(long long k, std::shared_ptr<Node> curr_solution);
    /*
        The generated tree structure will never be more than two deep.
        It checks for edges crossing between lower and higher k than the search k and returns the nodes above the cut.
        Edge case is when you have multiple children, some lower and some higher than search k. Then we merge to original node those that are higher.
        Original node is the one corresponding to the center cluster that all other children took from.
    */
    void get_k_solution_helper(long long k, std::shared_ptr<Node> fullTree, std::shared_ptr<Node> new_solution);
    /*
        Helper function that labels all nodes in a tree with given label using quick pointers.
    */
    void label_tree(std::vector<long long>& res, std::shared_ptr<Node> tree, long long label);

    /*
        This function takes the solution container (which is a "pseudo" node) and loops through its children of real solution nodes
        to output the cluster labels.
    */
    void extract_labels(std::vector<long long>& res, std::shared_ptr<Node> solution);

    // ########################## THRESHOLD CUTS ##############################

    /*
        This labels based on the highest node that is a cluster. The bottom_up_cluster algorithm labels all clusters that win as true bottom up.
        *THIS CAN ALSO BE USED WHEN NO IS_MERGER IS PRESENT, i.e. for HDBSCAN*
    */
    void label_clusters_helper_merge(std::shared_ptr<Node> tree, std::vector<long long>& labels, long long k);

    std::vector<long long> label_clusters_merge(std::shared_ptr<Node> tree, long long k = -1);
    /*
        Main threshold function.
        To make it perform kcenter cut even on the relaxed ultrametric, simply don't set is_cluster to false if node->cost > 0
    */
    void threshold_cut_main(std::vector<std::shared_ptr<Node>>& node_list, long long k, bool force_kcenter_cut = false);

    void trim_stem(std::vector<std::shared_ptr<Node>>& node_list);

    /*
        If provided with k = 0, this will use the elbow method to find it.
    */
    long long threshold(long long k = 0, bool stemTrim = false, bool force_kcenter_cut = false);
    void mark_tree_from_pruned(std::vector<std::shared_ptr<Node>> pruned_nodes);
    double stability(long long size, double pdist, double fallout_sum);

    // ################################ STABILITY HDBSCAN #####################################
    // This method ensures that we do not count noise branches in the split size
    long long split_size(std::shared_ptr<Node> tree, unsigned long long mcs);


    /*
    Uses merge_above to only compute stability at the top of cluster regions.
    */
    void bottom_up_cluster(std::shared_ptr<Node> fullTree, unsigned long long min_cluster_size);

    void bottom_up_cluster_normalized(std::shared_ptr<Node> fullTree, unsigned long long min_cluster_size);

public:
    unsigned long long get_elbow_k(bool triangle = true);
};

std::shared_ptr<Node> convertUltrametricTreeNodeToNode(std::shared_ptr<UltrametricTreeNode> ultrametricTreeRootNode);
