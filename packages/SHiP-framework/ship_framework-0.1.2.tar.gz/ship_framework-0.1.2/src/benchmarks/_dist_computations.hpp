#pragma once

#include <memory>
#include <vector>


// gcc -shared -o hdb.so hdb_c.c -O3 -march=native -lm -fopenmp -fPIC
/*
This code computes the core distances using quickselect,
and then computes the mutual reachability matrix from this.
*/

long long compare_doubles(const void *a, const void *b);

double euclidean_distance(std::vector<double> &x, std::vector<double> &y);

void calc_distance_matrix(std::vector<std::vector<double>> &data, double *distance_matrix);

void swap(double *const a, double *const b);

unsigned long long partition(double *const arr, const unsigned long long low, const unsigned long long high);

double quickSelect(double *const arr, const unsigned long long low, const unsigned long long high, const long long k);

void calc_core_dist_quickSelect(unsigned long long n, long long k, double *core_dist, double *distance_matrix);

void calc_core_dist_kdtree(std::vector<std::vector<double>> &data_c, long long k, double *core_dist);

double *calc_mutual_reachability_dist(std::vector<std::vector<double>> &data, double *core_dist);
