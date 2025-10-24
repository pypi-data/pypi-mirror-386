#pragma once

#include <framework/tree_structure.hpp>
#include <framework/tree_construction/ultrametric_tree_structure.hpp>
#include <memory>
#include <string>
#include <vector>


void printLabels(std::vector<long long> labels);
void print_vec(std::vector<double> vec);

void printSubtree(const std::string& prefix, const std::shared_ptr<Node>& tree);
void printTree(const std::shared_ptr<Node>& tree);

void printSubtree(const std::string& prefix, const std::shared_ptr<UltrametricTreeNode> tree);
void printTree(const std::shared_ptr<UltrametricTreeNode> tree);

void printSubtree_clusterMarkings(const std::string& prefix, const std::shared_ptr<Node>& tree);
void printTree_clusterMarkings(const std::shared_ptr<Node>& tree);

void printTree_k(const std::shared_ptr<Node>& tree);

void print_annotations(std::vector<Annotation*> annotations);
