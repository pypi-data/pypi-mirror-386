#include "mlpack_trees_adapter.hpp"

#include <pch.hpp>


template <typename TreeType>
std::shared_ptr<UltrametricTreeNode> convert_from_MLPackTree(const TreeType &root_MLPackTree, std::vector<size_t> &oldFromNew) {
    std::vector<std::pair<const TreeType &, std::shared_ptr<UltrametricTreeNode>>> stack;
    auto root = std::make_shared<UltrametricTreeNode>(-1, root_MLPackTree.FurthestDescendantDistance() * 2);
    stack.emplace_back(root_MLPackTree, root);
    while (!stack.empty()) {
        auto [mlTree, tree] = stack.back();
        stack.pop_back();
        for (size_t child_idx = 0; child_idx < mlTree.NumChildren(); child_idx++) {
            auto &child = mlTree.Child(child_idx);
            if (child.IsLeaf()) {
                for (size_t point_idx = 0; point_idx < child.NumPoints(); point_idx++) {
                    auto point = child.Point(point_idx);
                    auto leave_node = std::make_shared<UltrametricTreeNode>(static_cast<long long>(oldFromNew[point]), 0);
                    tree->children.push_back(leave_node);
                }
            } else {
                auto node = std::make_shared<UltrametricTreeNode>(-1, child.FurthestDescendantDistance() * 2);
                tree->children.push_back(node);
                stack.emplace_back(child, node);
            }
        }
    }
    return root;
}


std::shared_ptr<UltrametricTreeNode> convert_from_MLPackTree(std::vector<std::vector<double>> &data, UltrametricTreeType tree_type, const std::unordered_map<std::string, std::string> &config) {
    /*
        https://github.com/mlpack/mlpack/blob/master/doc/developer/trees.md
    */
    size_t min_leaf_size = get_config_value_in_range<size_t>(config, "min_leaf_size", 1, 1, data.size());
    size_t max_leaf_size = get_config_value_in_range<size_t>(config, "max_leaf_size", 5, 1, std::max(data.size(), static_cast<decltype(data.size())>(5)));

    size_t n = data.size();
    size_t dim = data[0].size();

    // Convert the c-array of the dataset into an arma::matrix.
    arma::mat armadata(dim, n);
    for (size_t i = 0; i < n; i++) {
        for (size_t j = 0; j < dim; j++) {
            armadata(j, i) = data[i][j];
        }
    }

    std::vector<size_t> oldFromNew(n);
    for (size_t i = 0; i < n; i++) {
        oldFromNew[i] = i;
    }

    switch (tree_type) {
        case UltrametricTreeType::CoverTree:
            return convert_from_MLPackTree(mlpack::StandardCoverTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata), oldFromNew);
        case UltrametricTreeType::KDTree:
            return convert_from_MLPackTree(mlpack::KDTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata, oldFromNew, max_leaf_size), oldFromNew);
        case UltrametricTreeType::MeanSplitKDTree:
            return convert_from_MLPackTree(mlpack::MeanSplitKDTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata, oldFromNew, max_leaf_size), oldFromNew);
        case UltrametricTreeType::BallTree:
            return convert_from_MLPackTree(mlpack::BallTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata, oldFromNew, max_leaf_size), oldFromNew);
        case UltrametricTreeType::MeanSplitBallTree:
            return convert_from_MLPackTree(mlpack::MeanSplitBallTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata, oldFromNew, max_leaf_size), oldFromNew);
        case UltrametricTreeType::RPTree:
            return convert_from_MLPackTree(mlpack::RPTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata, oldFromNew, max_leaf_size), oldFromNew);
        case UltrametricTreeType::MaxRPTree:
            return convert_from_MLPackTree(mlpack::MaxRPTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata, oldFromNew, max_leaf_size), oldFromNew);
        case UltrametricTreeType::UBTree:
            return convert_from_MLPackTree(mlpack::UBTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata, oldFromNew, max_leaf_size), oldFromNew);
        case UltrametricTreeType::RTree:
            return convert_from_MLPackTree(mlpack::RTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata, max_leaf_size, min_leaf_size), oldFromNew);
        case UltrametricTreeType::RStarTree:
            return convert_from_MLPackTree(mlpack::RStarTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata, max_leaf_size, min_leaf_size), oldFromNew);
        case UltrametricTreeType::XTree:
            return convert_from_MLPackTree(mlpack::XTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata, max_leaf_size, min_leaf_size), oldFromNew);
        case UltrametricTreeType::HilbertRTree:
            return convert_from_MLPackTree(mlpack::HilbertRTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata, max_leaf_size, min_leaf_size), oldFromNew);
        case UltrametricTreeType::RPlusTree:
            return convert_from_MLPackTree(mlpack::RPlusTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata, max_leaf_size, min_leaf_size), oldFromNew);
        case UltrametricTreeType::RPlusPlusTree:
            return convert_from_MLPackTree(mlpack::RPlusPlusTree<mlpack::EuclideanDistance, mlpack::EmptyStatistic, arma::mat>(armadata, max_leaf_size, min_leaf_size), oldFromNew);
        default:
            LOG_ERROR << "Selected MLPackTreeType '" << ultrametric_tree_type_to_string(tree_type) << "' is invalid!";
            throw std::invalid_argument("Invalid MLPackTreeType");
    }
}

UltrametricTree build_from_MLPackTree(std::vector<std::vector<double>> &data, UltrametricTreeType tree_type, const std::unordered_map<std::string, std::string> &config) {
    std::shared_ptr<UltrametricTreeNode> root = convert_from_MLPackTree(data, tree_type, config);
    return UltrametricTree{root, tree_type, config};
}
