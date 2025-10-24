#include <cmath>
#include <euclidean_methods.hpp>
#include <random>



using namespace std;

// Function to calculate Euclidean distance between two points
double euclideanDistance(const vector<double>& a, const vector<double>& b) {
    double sum = 0.0;
    for (long long i = 0; i < a.size(); ++i) {
        sum += pow(a[i] - b[i], 2);
    }
    return sqrt(sum);
}

// Function to add two vectors elementwise
vector<double> addVectors(const vector<double>& a, const vector<double>& b) {
    vector<double> c(a.size());
    long long n = a.size();

    for (long long i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }

    return c;
}

// Function to divide each element of a vector by a scalar
vector<double> divideVector(const vector<double>& a, double b) {
    vector<double> c(a.size());
    long long n = a.size();

    for (long long i = 0; i < n; ++i) {
        c[i] = a[i] / b;
    }

    return c;
}

vector<long long> assign_points_to_centers(vector<vector<double>>& points, vector<vector<double>>& centers) {
    // Reserve space for the result vector to avoid dynamic resizing
    std::vector<long long> res;
    res.reserve(points.size());

    for (long long point_idx = 0; point_idx < points.size(); ++point_idx) {
        const vector<double>& point = points[point_idx];

        double best_dist = numeric_limits<double>::max();
        long long best_cluster = -1;

        // Find the nearest cluster for the current point
        for (long long center_idx = 0; center_idx < centers.size(); ++center_idx) {
            const vector<double>& center = centers[center_idx];
            double dist = euclideanDistance(point, center);
            if (dist < best_dist) {
                best_dist = dist;
                best_cluster = center_idx;
            }
        }

        // Append the best cluster
        res.push_back(best_cluster);
    }
    return res;
}


// Farthest First Traversal function
std::vector<std::vector<double>> find_kcenters(std::vector<std::vector<double>>& points, long long k) {
    long long n = points.size();
    if (n == 0 || k <= 0 || k > n) {
        return {};
    }
    // Vector to store the k selected centers
    vector<vector<double>> centers;
    // Select the first center arbitrarily (here, the first point)
    centers.push_back(points[0]);
    // Vector to store the minimum distance of each point to any center
    vector<double> minDistances(n, numeric_limits<double>::max());

    for (long long i = 1; i < k; ++i) {
        // Update the minimum distances of each point to the current set of centers
        for (long long j = 0; j < n; ++j) {
            double dist = euclideanDistance(points[j], centers.back());
            minDistances[j] = min(minDistances[j], dist);
        }
        // Find the point with the maximum minimum distance
        long long farthestPointIndex = 0;
        double maxDist = -1;
        for (long long j = 0; j < n; ++j) {
            if (minDistances[j] > maxDist) {
                maxDist = minDistances[j];
                farthestPointIndex = j;
            }
        }
        // Add the farthest point as the next center
        centers.push_back(points[farthestPointIndex]);
    }
    return centers;
}



std::vector<long long> euclidean_k_center(std::vector<std::vector<double>>& points, long long k) {
    std::vector<std::vector<double>> centers = find_kcenters(points, k);
    return assign_points_to_centers(points, centers);
}


// K-means algorithm implementation
std::vector<std::vector<double>> find_kmeans(std::vector<std::vector<double>>& points, long long k) {
    static const double eps = 1e-4;
    static const long long max_iterations = 300;
    static std::random_device seed;
    static std::mt19937 rng(seed());
    std::uniform_int_distribution<long long> indices(0, points.size() - 1);

    // Pick initial centroids randomly from the dataset
    std::vector<std::vector<double>> means(k);
    for (auto& centroid : means) {
        centroid = points[indices(rng)];
    }

    std::vector<long long> assignments(points.size());
    std::vector<std::vector<double>> new_means(k, std::vector<double>(points[0].size(), 0.0));
    std::vector<long long> counts(k, 0);

    for (long long iteration = 0; iteration < max_iterations; ++iteration) {
        bool centroids_changed = false;

        // Reset new_means and counts for this iteration
        for (long long cluster = 0; cluster < k; ++cluster) {
            std::fill(new_means[cluster].begin(), new_means[cluster].end(), 0.0);
            counts[cluster] = 0;
        }

        // Assign points to the nearest centroid
        for (long long point = 0; point < points.size(); ++point) {
            double best_distance = std::numeric_limits<double>::max();
            long long best_cluster = 0;

            for (long long cluster = 0; cluster < k; ++cluster) {
                double distance = euclideanDistance(points[point], means[cluster]);
                if (distance < best_distance) {
                    best_distance = distance;
                    best_cluster = cluster;
                }
            }

            assignments[point] = best_cluster;
            new_means[best_cluster] = addVectors(new_means[best_cluster], points[point]);
            counts[best_cluster] += 1;
        }

        // Update centroids
        for (long long cluster = 0; cluster < k; ++cluster) {
            if (counts[cluster] > 0) {
                // Avoid division by zero and update centroid only if the cluster has points
                std::vector<double> updated_centroid = divideVector(new_means[cluster], counts[cluster]);

                if (euclideanDistance(means[cluster], updated_centroid) > eps) {
                    centroids_changed = true;
                }
                means[cluster] = updated_centroid;
            }
        }

        // Early stopping if centroids did not change significantly
        if (!centroids_changed) {
            break;
        }
    }

    return means;
}

std::vector<long long> euclidean_k_means(std::vector<std::vector<double>>& points, long long k) {
    std::vector<std::vector<double>> centers = find_kmeans(points, k);
    return assign_points_to_centers(points, centers);
}
