#include "elbow_methods.hpp"

#include <framework/tree_structure.hpp>
#include <pch.hpp>


unsigned long long elbow_triangle(std::vector<double>& costs) {
    unsigned long long n = costs.size();
    unsigned long long elbowIndex = 0;
    double maxVal = std::numeric_limits<double>::max();
    double cost_0 = costs[0];  // Start cost
    double cost_n = costs[costs.size() - 1];
    for (unsigned long long k = 2; k < n; k++) {
        Point v1 = {0.0 - (double)k, (cost_0 - costs[k]) / cost_0 * (double)n};
        Point v2 = {((double)n - 1.0) - (double)k, (cost_n - costs[k]) / cost_0 * (double)n};

        double pi = 3.14159265358;
        double val = std::acos((v1.x * v2.x + v1.y * v2.y) / (std::sqrt(v1.x * v1.x + v1.y * v1.y) * std::sqrt(v2.x * v2.x + v2.y * v2.y))) * (180 / pi);

        if (val < maxVal) {
            maxVal = val;
            elbowIndex = k;
        }
    }
    return elbowIndex;
}


/*
    Returns the k that is the elbow of the values
    The distance computation has been hand checked to be correct. Code structure found on geeks for geeks.
*/
unsigned long long elbow_line_dist(std::vector<double>& costs) {
    unsigned long long n = costs.size();
    unsigned long long elbowIndex = 0;
    double maxDist = -std::numeric_limits<double>::max();

    double line_start_y = costs[0];
    double line_end_y = costs[n - 1];

    std::pair<double, double> AB;  // AB = segment between first and last point - x going from 0 to n-1
    AB.first = (double)n - 1;
    AB.second = line_end_y - line_start_y;

    unsigned long long i = 0;
    for (double cost : costs) {
        if (i == 0 || i == n - 1) {
            i++;
            continue;
        }
        double x0 = (double)i;
        double y0 = cost;
        std::pair<double, double> BE;
        BE.first = x0 - ((double)n - 1);
        BE.second = y0 - line_end_y;

        std::pair<double, double> AE;  // vector AP
        AE.first = x0;
        AE.second = y0 - line_start_y;

        double x1 = AB.first;  // Finding the perpendicular distance
        double y1 = AB.second;
        double x2 = AE.first;
        double y2 = AE.second;
        double mod = std::sqrt(x1 * x1 + y1 * y1);
        double dist = std::abs(x1 * y2 - y1 * x2) / mod;

        if (dist > maxDist) {
            maxDist = dist;
            elbowIndex = i + 1;
        } else {
            // If distance is not larger than maxDist, it means that distances are now decreasing - no need to check further
            break;
        }
        i++;
    }
    return elbowIndex;
}


unsigned long long Tree::get_elbow_k(bool triangle) {
    bool elbow_use_costs = get_config_value(this->config, "elbow_use_costs", true);
    std::vector<double>& values = elbow_use_costs ? this->costs : this->cost_decreases;

    if (triangle) {
        return elbow_triangle(values);
    } else {
        return elbow_line_dist(values);
    }
}
