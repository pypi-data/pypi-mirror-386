#pragma once
#include <framework/tree_structure.hpp>
#include <vector>

struct Point {
    double x, y;
};

// Compute the elbow by finding the point creating closest to a right angle
unsigned long long elbow_triangle(std::vector<double>& costs);

// Compute the elbow by finding the point furthest from the line from first to last value
unsigned long long elbow_line_dist(std::vector<double>& costs);

// std::vector<double> Tree::get_elbow_data(std::string method);
