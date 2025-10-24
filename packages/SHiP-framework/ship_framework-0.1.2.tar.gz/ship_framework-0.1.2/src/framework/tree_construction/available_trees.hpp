#pragma once

#include <array>
#include <string>
#include <utility>
#include <vector>


/*!
 * \brief Types of ultrametric trees available in the SHiP framework.
 *
 * Enum class `UltrametricTreeType` representing supported ultrametric trees types.
 */
enum class UltrametricTreeType {
    /// Load a previously constructed tree from a JSON file.
    ///
    /// **Parameters:**
    /// - `json_tree_filepath`: File path of the tree to be loaded.
    /// - `tree_type` (default: `LoadTree`, optional): Set the tree type of the loaded tree to `tree_type`.
    LoadTree,

    /// Density-Connected Tree (DCTree): a tree structure based on the density-connected distance (dc-distance). \rst:ref:`[1]<dc-dist>`\endrst.
    ///
    /// **Parameters:**
    /// - `min_points` (default: `5`): Compute *core_dist* by using the distance to the min_points' nearest neighbor of a point.
    /// - `relaxed` (default: `true`): Set the identity distance of the points (leave nodes) to the *core_dist*.
    DCTree,

    /// Hierarchically Separated Tree (HST): uses recursive metric partitions to ensure separation properties \rst:ref:`[2]<hst>`\endrst.
    ///
    /// **Parameters:**
    /// - `seed` (default: `-1`): Seed for building the HST. `-1` means random.
    HST,

    /// Cover Tree: a fast, scalable data structure for nearest neighbor queries and clustering \rst:ref:`[3]<mlpack>`\endrst.
    CoverTree,

    /// KD-Tree: partitions the data space along axis-aligned hyperplanes for efficient spatial queries \rst:ref:`[3]<mlpack>`\endrst.
    ///
    /// **Parameters:**
    /// - `max_leaf_size` (default: `5`): Maximum leaf size for this tree (how many leaves can be put in the lowest node).
    KDTree,

    /// Variant of KD-Tree using mean splits instead of medians to construct the tree \rst:ref:`[3]<mlpack>`\endrst.
    ///
    /// **Parameters:**
    /// - `max_leaf_size` (default: `5`): Maximum leaf size for this tree (how many leaves can be put in the lowest node).
    MeanSplitKDTree,

    /// Ball Tree: recursively partitions points into hyperspheres (balls), suitable for non-axis-aligned clusters \rst:ref:`[3]<mlpack>`\endrst.
    ///
    /// **Parameters:**
    /// - `max_leaf_size` (default: `5`): Maximum leaf size for this tree (how many leaves can be put in the lowest node).
    BallTree,

    /// Variant of Ball Tree that uses mean splits instead of radius-based ones \rst:ref:`[3]<mlpack>`\endrst.
    ///
    /// **Parameters:**
    /// - `max_leaf_size` (default: `5`): Maximum leaf size for this tree (how many leaves can be put in the lowest node).
    MeanSplitBallTree,

    /// Random Projection Tree (RP Tree): recursively splits data using random hyperplanes \rst:ref:`[3]<mlpack>`\endrst.
    ///
    /// **Parameters:**
    /// - `max_leaf_size` (default: `5`): Maximum leaf size for this tree (how many leaves can be put in the lowest node).
    RPTree,

    /// Maximum-Spread RP Tree: a variant of RP Tree using splits that maximize spread or variance \rst:ref:`[3]<mlpack>`\endrst.
    ///
    /// **Parameters:**
    /// - `max_leaf_size` (default: `5`): Maximum leaf size for this tree (how many leaves can be put in the lowest node).
    MaxRPTree,

    /// Upper Bound Tree (UBTree): a tree structure emphasizing similarity upper bounds for clustering \rst:ref:`[3]<mlpack>`\endrst.
    ///
    /// **Parameters:**
    /// - `max_leaf_size` (default: `5`): Maximum leaf size for this tree (how many leaves can be put in the lowest node).
    UBTree,

    /// R-Tree: a dynamic index structure for spatial access methods using bounding rectangles \rst:ref:`[3]<mlpack>`\endrst.
    ///
    /// **Parameters:**
    /// - `min_leaf_size` (default: `1`): Minimum leaf size for this tree (how many leaves can be put in the lowest node).
    /// - `max_leaf_size` (default: `5`): Maximum leaf size for this tree (how many leaves can be put in the lowest node).
    RTree,

    /// R*-Tree: a refined R-Tree with better heuristics for node splitting and reinsertions \rst:ref:`[3]<mlpack>`\endrst.
    ///
    /// **Parameters:**
    /// - `min_leaf_size` (default: `1`): Minimum leaf size for this tree (how many leaves can be put in the lowest node).
    /// - `max_leaf_size` (default: `5`): Maximum leaf size for this tree (how many leaves can be put in the lowest node).
    RStarTree,

    /// X-Tree: an extended R-Tree variant that handles high-dimensional data by avoiding overlap \rst:ref:`[3]<mlpack>`\endrst.
    ///
    /// **Parameters:**
    /// - `min_leaf_size` (default: `1`): Minimum leaf size for this tree (how many leaves can be put in the lowest node).
    /// - `max_leaf_size` (default: `5`): Maximum leaf size for this tree (how many leaves can be put in the lowest node).
    XTree,

    /// Hilbert R-Tree: an R-Tree optimized using space-filling Hilbert curves to improve locality \rst:ref:`[3]<mlpack>`\endrst.
    ///
    /// **Parameters:**
    /// - `min_leaf_size` (default: `1`): Minimum leaf size for this tree (how many leaves can be put in the lowest node).
    /// - `max_leaf_size` (default: `5`): Maximum leaf size for this tree (how many leaves can be put in the lowest node).
    HilbertRTree,

    /// R+-Tree: avoids overlapping rectangles by splitting objects across multiple nodes \rst:ref:`[3]<mlpack>`\endrst.
    ///
    /// **Parameters:**
    /// - `min_leaf_size` (default: `1`): Minimum leaf size for this tree (how many leaves can be put in the lowest node).
    /// - `max_leaf_size` (default: `5`): Maximum leaf size for this tree (how many leaves can be put in the lowest node).
    RPlusTree,

    /// R++-Tree: a further improvement over R+-Tree focusing on reduced overlap and better packing \rst:ref:`[3]<mlpack>`\endrst.
    ///
    /// **Parameters:**
    /// - `min_leaf_size` (default: `1`): Minimum leaf size for this tree (how many leaves can be put in the lowest node).
    /// - `max_leaf_size` (default: `5`): Maximum leaf size for this tree (how many leaves can be put in the lowest node).
    RPlusPlusTree
};


// Helper: Array of UltrametricTreeType-string pairs
constexpr std::array<std::pair<UltrametricTreeType, std::string_view>, 17> ultrametricTreeTypeStrings = {{
    {UltrametricTreeType::LoadTree, "LoadTree"},
    {UltrametricTreeType::DCTree, "DCTree"},
    {UltrametricTreeType::HST, "HST"},
    {UltrametricTreeType::CoverTree, "CoverTree"},
    {UltrametricTreeType::KDTree, "KDTree"},
    {UltrametricTreeType::MeanSplitKDTree, "MeanSplitKDTree"},
    {UltrametricTreeType::BallTree, "BallTree"},
    {UltrametricTreeType::MeanSplitBallTree, "MeanSplitBallTree"},
    {UltrametricTreeType::RPTree, "RPTree"},
    {UltrametricTreeType::MaxRPTree, "MaxRPTree"},
    {UltrametricTreeType::UBTree, "UBTree"},
    {UltrametricTreeType::RTree, "RTree"},
    {UltrametricTreeType::RStarTree, "RStarTree"},
    {UltrametricTreeType::XTree, "XTree"},
    {UltrametricTreeType::HilbertRTree, "HilbertRTree"},
    {UltrametricTreeType::RPlusTree, "RPlusTree"},
    {UltrametricTreeType::RPlusPlusTree, "RPlusPlusTree"},
}};


// From UltrametricTreeType to string
std::string ultrametric_tree_type_to_string(UltrametricTreeType type);

// From string to UltrametricTreeType
UltrametricTreeType string_to_ultrametric_tree_type(const std::string& type);

// Get all available UltrametricTreeTypes
std::vector<UltrametricTreeType> get_available_ultrametric_tree_types();

// Get all available UltrametricTreeTypes as strings
std::vector<std::string> get_available_ultrametric_tree_types_as_strings();
