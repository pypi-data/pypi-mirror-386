//
// C++ standalone verion of fastcluster by Daniel Müllner
//
// Copyright: Christoph Dalitz, 2020
//            Daniel Müllner, 2011
// License:   BSD style license
//            (see the file LICENSE for details)
//
// from https://github.com/cdalitz/hclust-cpp/blob/master/fastcluster.cpp

#include <agglomerative.hpp>
#include <algorithm>
#include <vector>


// Code by Daniel Müllner
// workaround to make it usable as a standalone version (without R)
bool fc_isnan(double x) { return x != x; }
#include "fastcluster_R_dm.cpp"

using namespace std;

//
// Assigns cluster labels (0, ..., nclust-1) to the n points such
// that the cluster result is split into nclust clusters.
//
// Input arguments:
//   n      = number of observables
//   merge  = clustering result in R format
//   nclust = number of clusters
// Output arguments:
//   labels = allocated integer array of size n for result
//
void cutree_k(long long n, long long* merge, long long nclust, long long* labels) {
    long long k, m1, m2, j, l;

    if (nclust > n || nclust < 2) {
        for (j = 0; j < n; j++) labels[j] = 0;
        return;
    }

    // assign to each observable the number of its last merge step
    // beware: indices of observables in merge start at 1 (R convention)
    std::vector<long long> last_merge(n, 0);
    for (k = 1; k <= (n - nclust); k++) {
        // (m1,m2) = merge[k,]
        m1 = merge[k - 1];
        m2 = merge[n - 1 + k - 1];
        if (m1 < 0 && m2 < 0) {  // both single observables
            last_merge[-m1 - 1] = last_merge[-m2 - 1] = k;
        } else if (m1 < 0 || m2 < 0) {  // one is a cluster
            if (m1 < 0) {
                j = -m1;
                m1 = m2;
            } else
                j = -m2;
            // merging single observable and cluster
            for (l = 0; l < n; l++)
                if (last_merge[l] == m1)
                    last_merge[l] = k;
            last_merge[j - 1] = k;
        } else {  // both cluster
            for (l = 0; l < n; l++) {
                if (last_merge[l] == m1 || last_merge[l] == m2)
                    last_merge[l] = k;
            }
        }
    }

    // assign cluster labels
    long long label = 0;
    std::vector<long long> z(n, -1);
    for (j = 0; j < n; j++) {
        if (last_merge[j] == 0) {  // still singleton
            labels[j] = label++;
        } else {
            if (z[last_merge[j]] < 0) {
                z[last_merge[j]] = label++;
            }
            labels[j] = z[last_merge[j]];
        }
    }
}

//
// Assigns cluster labels (0, ..., nclust-1) to the n points such
// that the hierarchical clustering is stopped when cluster distance >= cdist
//
// Input arguments:
//   n      = number of observables
//   merge  = clustering result in R format
//   height = cluster distance at each merge step
//   cdist  = cutoff cluster distance
// Output arguments:
//   labels = allocated integer array of size n for result
//
void cutree_cdist(long long n, long long* merge, double* height, double cdist, long long* labels) {
    long long k;

    for (k = 0; k < (n - 1); k++) {
        if (height[k] >= cdist) {
            break;
        }
    }
    cutree_k(n, merge, n - k, labels);
}


//
// Hierarchical clustering with one of Daniel Muellner's fast algorithms
//
// Input arguments:
//   n       = number of observables
//   distmat = condensed distance matrix, i.e. an n*(n-1)/2 array representing
//             the upper triangle (without diagonal elements) of the distance
//             matrix, e.g. for n=4:
//               d00 d01 d02 d03
//               d10 d11 d12 d13   ->  d01 d02 d03 d12 d13 d23
//               d20 d21 d22 d23
//               d30 d31 d32 d33
//   method  = cluster metric (see enum hclust_fast_methods)
// Output arguments:
//   merge   = allocated (n-1)x2 matrix (2*(n-1) array) for storing result.
//             Result follows R hclust convention:
//              - observabe indices start with one
//              - merge[i][] contains the merged nodes in step i
//              - merge[i][j] is negative when the node is an atom
//   height  = allocated (n-1) array with distances at each merge step
// Return code:
//   0 = ok
//   1 = invalid method
//
long long hclust_fast(long long n, double* distmat, long long method, long long* merge, double* height) {
    // call appropriate culstering function
    cluster_result Z2(n - 1);
    if (method == HCLUST_METHOD_SINGLE) {
        // single link
        MST_linkage_core(n, distmat, Z2);
    } else if (method == HCLUST_METHOD_COMPLETE) {
        // complete link
        NN_chain_core<METHOD_METR_COMPLETE, t_float>(n, distmat, NULL, Z2);
    } else if (method == HCLUST_METHOD_AVERAGE) {
        // best average distance
        double* members = new double[n];
        for (long long i = 0; i < n; i++) members[i] = 1;
        NN_chain_core<METHOD_METR_AVERAGE, t_float>(n, distmat, members, Z2);
        delete[] members;
    } else if (method == HCLUST_METHOD_MEDIAN) {
        // best median distance (beware: O(n^3))
        generic_linkage<METHOD_METR_MEDIAN, t_float>(n, distmat, NULL, Z2);
    } else {
        return 1;
    }

    long long* order = new long long[n];
    if (method == HCLUST_METHOD_MEDIAN) {
        generate_R_dendrogram<true>(merge, height, order, Z2, n);
    } else {
        generate_R_dendrogram<false>(merge, height, order, Z2, n);
    }

    delete[] order;  // only needed for visualization

    return 0;
}


// Function to calculate Euclidean distance between two points using OpenMP
double euclideanDistance2(const std::vector<double>& a, const std::vector<double>& b) {
    double sum = 0.0;
    long long n = a.size();  // Assume both vectors are of the same size

    // Parallelize the loop using OpenMP
    // #pragma omp parallel for reduction(+:sum)
    for (long long i = 0; i < n; ++i) {
        sum += pow(a[i] - b[i], 2);
    }

    return sqrt(sum);
}



vector<double> calc_distmat(vector<vector<double>>& x) {
    vector<double> distmat((x.size() * (x.size() - 1)) / 2);
    long long k, i, j;
    for (i = k = 0; i < x.size(); i++) {
        for (j = i + 1; j < x.size(); j++) {
            // compute distance between observables i and j
            distmat[k] = euclideanDistance2(x[i], x[j]);
            k++;
        }
    }
    return distmat;
}


std::vector<long long> agglomerative_clustering(std::vector<std::vector<double>>& points, long long k, long long method) {
    vector<double> distmat = calc_distmat(points);

    vector<long long> merge(2 * (points.size() - 1));
    vector<double> height(points.size() - 1);
    hclust_fast(points.size(), distmat.data(), method, merge.data(), height.data());

    vector<long long> labels(points.size());
    // partitioning into nclust clusters
    cutree_k(points.size(), merge.data(), k, labels.data());
    return labels;
}
