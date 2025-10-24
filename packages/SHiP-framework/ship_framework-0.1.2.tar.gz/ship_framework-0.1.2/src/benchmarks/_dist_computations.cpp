#include "_dist_computations.hpp"

#include <pch.hpp>


void swap(double *const a, double *const b) {
    double temp = *a;
    *a = *b;
    *b = temp;
}

unsigned long long partition(double *const arr, const unsigned long long low, const unsigned long long high) {
    const double pivot = arr[high];
    unsigned long long i = low - 1;

    for (unsigned long long j = low; j < high; j++) {
        if (arr[j] <= pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }

    swap(&arr[i + 1], &arr[high]);
    return i + 1;
}

double quickSelect(double *const arr, const unsigned long long low, const unsigned long long high, const long long k) {
    if (low <= high) {
        const long long pivotIndex = partition(arr, low, high);

        if (pivotIndex == k) {
            return arr[pivotIndex];
        } else if (pivotIndex < k) {
            return quickSelect(arr, pivotIndex + 1, high, k);
        } else {
            return quickSelect(arr, low, pivotIndex - 1, k);
        }
    }

    return -1.0;
}


void calc_core_dist_quickSelect(unsigned long long n, long long k, double *core_dist, double *distance_matrix) {
    // #pragma omp parallel for
    for (unsigned long long i = 0; i < n; i++) {
        double *temp_array = (double *)malloc(n * sizeof(double));
        memcpy(temp_array, &distance_matrix[i * n], n * sizeof(double));
        core_dist[i] = quickSelect(temp_array, 0, n - 1, k - 1);
    }
}




double euclidean_distance(std::vector<double> &x, std::vector<double> &y) {
    double sum = 0.0;

    for (unsigned long long i = 0; i < x.size(); i++) {
        double diff = x[i] - y[i];
        sum += diff * diff;
    }
    return sqrt(sum);
    // return sum;
}

void calc_distance_matrix(std::vector<std::vector<double>> &data, double *distance_matrix) {
    unsigned long long n = data.size();
    // #pragma omp parallel for schedule(dynamic, 4)
    for (unsigned long long i = 0; i < n; i++) {
        for (unsigned long long j = 0; j < n; j++) {
            double distance = euclidean_distance(data[i], data[j]);
            distance_matrix[i * n + j] = distance;
        }
    }
    // #pragma omp parallel for schedule(dynamic, 2)
    for (unsigned long long i = 0; i < n; i++) {
        for (unsigned long long j = 0; j < i; j++) {
            distance_matrix[i * n + j] = distance_matrix[j * n + i];
        }
    }
}



/*
    Computes the core distance vector using the mlpack kdtree structure.
    Takes as input the dataset and pupulates the provided core_dist c-array.
    TODO: If k=1, just return an array of 0.
*/
void calc_core_dist_kdtree(std::vector<std::vector<double>> &data_c, long long k, double *core_dist) {
    long long rows = data_c.size();
    long long cols = data_c[0].size();

    // Allocate flat vector in column-major order
    std::vector<double> flat_data(rows * cols);

    // Fill flat_data in column-major order
    for (long long j = 0; j < cols; ++j) {
        for (long long i = 0; i < rows; ++i) {
            flat_data[j * rows + i] = data_c[i][j];
        }
    }

    // Construct arma::mat from flat_data, without copying (false)
    arma::mat data(flat_data.data(), rows, cols, false, true);  // rows, cols order, matches layout

    mlpack::NeighborSearch<mlpack::NearestNeighborSort, mlpack::EuclideanDistance, arma::mat, mlpack::KDTree> knn(data);
    arma::Mat<size_t> neighbors;
    arma::mat distances;
    if (k <= 1) {
        k = 2;
    }
    knn.Search(k - 1, neighbors, distances);  // This does not include point itself in k, which is why we do k-1

    for (unsigned long long i = 0; i < distances.n_cols; i++) {
        arma::vec col = distances.col(i);
        core_dist[i] = col(k - 2);
    }
}


/*
    Computes the Mutual Reachability Distance matrix.
    Takes as input the dataset and the vector of core dists.
    Outputs the mututal reachability distances as an n x n double array.

*/
double *calc_mutual_reachability_dist(std::vector<std::vector<double>> &data, double *core_dist) {
    unsigned long long n = data.size();
    double *distance_matrix = (double *)malloc(n * n * sizeof(double));
    double *mutual_reach_dist = (double *)malloc(n * n * sizeof(double));

    calc_distance_matrix(data, distance_matrix);
    // #pragma omp parallel for  // schedule(static, 2)
    for (unsigned long long i = 0; i < n; i++) {
        for (unsigned long long j = i + 1; j < n; j++) {
            mutual_reach_dist[i * n + j] = fmax(fmax(core_dist[i], core_dist[j]), distance_matrix[i * n + j]);
            mutual_reach_dist[j * n + i] = mutual_reach_dist[i * n + j];
        }
    }
    free(distance_matrix);
    return mutual_reach_dist;
}