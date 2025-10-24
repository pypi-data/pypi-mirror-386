/**
    \author:    Trasier
    \date:        2019.6.18
*/
#pragma once

#include <utility>
#include <vector>


typedef long long LL;
typedef std::pair<long long, long long> pii;
typedef std::pair<double, double> pdd;
typedef std::pair<long long, double> pid;
typedef std::pair<double, long long> pdi;

typedef std::vector<double> location_t;

extern long long nV;
extern std::vector<location_t>& V;
extern const double speed;
extern const double EPS;
extern const double INF;
extern double usedTime;
extern long long usedMemory;
extern double timeLimit;
extern double squaredScaleFactor;

long long dcmp(double x);
double dist(std::vector<location_t>& V, long long x, long long y);
double dist(location_t& a, location_t& b);
