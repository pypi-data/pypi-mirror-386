/**
    \author:    Trasier
    \date:        2019.6.18
*/
#include "global.hpp"

#include <cmath>


long long nV = 0;
std::vector<location_t>& V = *(new std::vector<std::vector<double>>());
;
const double speed = 1.0;
const double EPS = 1e-5;
const double INF = 1e20;
double usedTime = 0.0;
long long usedMemory = 0;
double timeLimit = 10 * 24 * 60 * 60;  // 10 days
double squaredScaleFactor = 1.0;

long long dcmp(double x) {
    if (std::fabs(x) < EPS)
        return 0;
    return x > 0 ? 1 : -1;
}

double dist(std::vector<location_t>& V, long long x, long long y) {
    if (x == y) return 0;

    location_t& a = V[x];
    location_t& b = V[y];
    double ret = 0.0;

    for (unsigned long long i = 0; i < V[0].size(); ++i) {
        ret += (a[i] - b[i]) * (a[i] - b[i]) / squaredScaleFactor;
    }

    return std::sqrt(ret);
}

double dist(location_t& a, location_t& b) {
    double ret = 0.0;

    for (unsigned long long i = 0; i < V[0].size(); ++i) {
        ret += (a[i] - b[i]) * (a[i] - b[i]) / squaredScaleFactor;
    }

    return std::sqrt(ret);
}
