#pragma once

#include <memory>
#include <vector>


struct Node;  // Forward declaration for circular dependencies


/*
    This labels based on the highest node that is a cluster. The bottom_up_cluster algorithm labels all clusters that win as true bottom up.
    So we should only increase ctr when it is a topmost cluster.

    This method labels clusters based on the is_cluster field of the internal nodes of a tree.
    It bases the labelling on the first "true" encountered top down and ignores those further down.

*/
std::vector<long long> label_clusters(std::shared_ptr<Node> tree);


/*
    Resets markings in the tree used for labelling the final clusterings.
    Can both be used for SHiP/HDBSCAN and center-based labellings.
*/
void clean_tree(std::shared_ptr<Node> tree);

std::shared_ptr<Node> prune_tree(std::shared_ptr<Node>& tree, long long minPts);
std::vector<std::shared_ptr<Node>> prune_tree_fast(std::vector<std::shared_ptr<Node>>& nodes, unsigned long long minPts);
