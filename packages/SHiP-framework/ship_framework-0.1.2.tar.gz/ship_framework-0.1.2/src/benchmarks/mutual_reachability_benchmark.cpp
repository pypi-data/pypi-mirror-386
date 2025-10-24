#include <omp.h>

#include <algorithm>
#include <chrono>
#include <benchmarks/_dist_computations.hpp>
#include <iostream>
#include <mlpack/core.hpp>
#include <mlpack/core/metrics/metrics.hpp>
#include <mlpack/core/tree/statistic.hpp>
#include <mlpack/core/tree/tree.hpp>
#include <mlpack/methods/neighbor_search/neighbor_search.hpp>
#include <vector>


arma::mat version_kdtree(const arma::mat& data, int k, std::vector<double>& core_dists) {
    if (k <= 1) k = 2;

    mlpack::NeighborSearch<mlpack::NearestNeighborSort, mlpack::EuclideanDistance, arma::mat, mlpack::KDTree> knn(data);
    arma::Mat<size_t> neighbors;
    arma::mat distances;
    knn.Search(k - 1, neighbors, distances);  // This does not include point itself in k, which is why we do k-1

    for (unsigned long long i = 0; i < distances.n_cols; i++) {
        core_dists[i] = distances(k - 2, i);
    }

    // Get matrix dimensions
    const size_t n_rows = data.n_rows;
    const size_t n_cols = data.n_cols;

    std::vector<std::vector<double>> vecData(data.n_cols, std::vector<double>(data.n_rows));
    for (size_t i = 0; i < data.n_cols; ++i) {
        for (size_t j = 0; j < data.n_rows; ++j) {
            vecData[i][j] = data(j, i);  // Access by (row, col)
        }
    }
    auto mr_dists = calc_mutual_reachability_dist(vecData, core_dists.data());

    arma::mat mat(data.n_cols, data.n_cols);  // Armadillo allocates column-major
    for (size_t i = 0; i < data.n_cols; ++i) {
        for (size_t j = 0; j < data.n_cols; ++j) {
            mat(i, j) = mr_dists[i * data.n_cols + j];  // Same layout: (row, col)
        }
    }
    for (size_t i = 0; i < data.n_cols; ++i) {
        mat(i, i) = 0.0;
    }
    return mat;
}

void version_covertree(const arma::mat& data, int k, std::vector<double>& core_dists) {
    if (k <= 1) k = 2;

    mlpack::NeighborSearch<mlpack::NearestNeighborSort, mlpack::EuclideanDistance, arma::mat, mlpack::CoverTree> knn(data);
    arma::Mat<size_t> neighbors;
    arma::mat distances;
    knn.Search(k - 1, neighbors, distances);  // This does not include point itself in k, which is why we do k-1

    for (unsigned long long i = 0; i < distances.n_cols; i++) {
        core_dists[i] = distances(k - 2, i);
    }
}

arma::mat version_scalar(const arma::mat& data, int k, std::vector<double>& core_dists) {
    if (k <= 1) k = 2;

    int n = data.n_cols;
    arma::mat dists(n, n, arma::fill::none);
    for (size_t i = 0; i < n; ++i) {
        dists(i, i) = 0.0;
    }

    // Stage 1: Parallel fill upper triangle (j > i)
    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            double dist = arma::norm(data.col(i) - data.col(j), 2);
            dists(i, j) = dist;
        }
    }

    // Stage 2: Compute core distances
    for (int i = 0; i < n; ++i) {
        std::vector<double> knn_dists;
        knn_dists.reserve(n - 1);

        for (int j = 0; j < i; ++j) {
            knn_dists.push_back(dists(j, i));
        }
        for (int j = i + 1; j < n; ++j) {
            knn_dists.push_back(dists(i, j));
        }

        std::nth_element(knn_dists.begin(), knn_dists.begin() + (k - 2), knn_dists.end());
        core_dists[i] = knn_dists[k - 2];
    }

    // Stage 3: Parallel fill lower triangle (j < i)
    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            dists(j, i) = dists(i, j);
        }
    }

    // Stage 4: Compute mutual-reachability distances
    // mutual-reachability distance
    arma::vec core_vec(core_dists);

    for (size_t j = 0; j < n; ++j) {
        dists.col(j) = arma::max(dists.col(j), core_vec);
    }
    for (size_t i = 0; i < n; ++i) {
        dists.row(i) = arma::max(dists.row(i), core_vec.t());
    }
    for (size_t i = 0; i < n; ++i) {
        dists(i, i) = 0.0;
    }
    return dists;
}

arma::mat version_scalar_openmp(const arma::mat& data, int k, std::vector<double>& core_dists) {
    if (k <= 1) k = 2;

    int n = data.n_cols;
    arma::mat dists(n, n, arma::fill::none);
#pragma omp parallel for schedule(static)
    for (size_t i = 0; i < n; ++i) {
        dists(i, i) = 0.0;
    }

    // Stage 1: Parallel fill upper triangle (j > i)
#pragma omp parallel for schedule(guided)
    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            double dist = arma::norm(data.col(i) - data.col(j), 2);
            dists(i, j) = dist;
        }
    }

    // Stage 2: Compute core distances
#pragma omp parallel for schedule(static)
    for (int i = 0; i < n; ++i) {
        std::vector<double> knn_dists;
        knn_dists.reserve(n - 1);

        for (int j = 0; j < i; ++j) {
            knn_dists.push_back(dists(j, i));
        }
        for (int j = i + 1; j < n; ++j) {
            knn_dists.push_back(dists(i, j));
        }

        std::nth_element(knn_dists.begin(), knn_dists.begin() + (k - 2), knn_dists.end());
        core_dists[i] = knn_dists[k - 2];
    }

    // Stage 3: Parallel fill lower triangle (j < i)
#pragma omp parallel for schedule(guided)
    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            dists(j, i) = dists(i, j);
        }
    }

    // Stage 4: Compute mutual-reachability distances
    // mutual-reachability distance
    arma::vec core_vec(core_dists);

#pragma omp parallel for schedule(static)
    for (size_t j = 0; j < n; ++j) {
        dists.col(j) = arma::max(dists.col(j), core_vec);
    }
#pragma omp parallel for schedule(static)
    for (size_t i = 0; i < n; ++i) {
        dists.row(i) = arma::max(dists.row(i), core_vec.t());
    }
#pragma omp parallel for schedule(static)
    for (size_t i = 0; i < n; ++i) {
        dists(i, i) = 0.0;
    }
    return dists;
}

void version_vectorized(const arma::mat& data, int k, std::vector<double>& core_dists) {
    int n = data.n_cols;

    for (int i = 0; i < n; ++i) {
        arma::vec diff = arma::sum(arma::square(data.each_col() - data.col(i)), 0).t();
        diff.shed_row(i);

        std::vector<double> distances(diff.begin(), diff.end());
        std::nth_element(distances.begin(), distances.begin() + (k - 1), distances.end());
        core_dists[i] = std::sqrt(distances[k - 1]);
    }
}

void version_vectorized_openmp(const arma::mat& data, int k, std::vector<double>& core_dists) {
    int n = data.n_cols;

#pragma omp parallel for schedule(static)
    for (int i = 0; i < n; ++i) {
        arma::vec diff = arma::sum(arma::square(data.each_col() - data.col(i)), 0).t();
        diff.shed_row(i);

        std::vector<double> distances(diff.begin(), diff.end());
        std::nth_element(distances.begin(), distances.begin() + (k - 1), distances.end());
        core_dists[i] = std::sqrt(distances[k - 1]);
    }
}

void benchmark(int n_points, int dim, int k, bool print = true) {
    arma::mat data = arma::randu(dim, n_points);
    std::vector<double> core_dists_ref(n_points);
    std::vector<double> core_dists(n_points);
    arma::mat mr_dists_ref;
    arma::mat mr_dists;
    double ref_time = 0.0;

    auto run = [&](auto func, const std::string& label, bool is_reference = false) {
        auto start = std::chrono::high_resolution_clock::now();
        mr_dists = func(data, k, core_dists);
        asm volatile(""
                     :
                     : "r,m"(core_dists)
                     : "memory");
        auto end = std::chrono::high_resolution_clock::now();
        double ms = std::chrono::duration<double, std::milli>(end - start).count();

        if (is_reference) {
            mr_dists_ref = mr_dists;
            ref_time = ms;
            core_dists_ref = core_dists;  // Save reference
        } else {
            // Compare against reference (tolerance for floating point comparison)
            for (size_t i = 0; i < core_dists.size(); ++i) {
                if (std::abs(core_dists[i] - core_dists_ref[i]) > 1e-8) {
                    std::cerr << "Mismatch at index " << i << " for " << label
                              << ": got " << core_dists[i]
                              << ", expected " << core_dists_ref[i] << "\n";
                    std::exit(EXIT_FAILURE);
                }
            }

            if (!approx_equal(mr_dists_ref, mr_dists, "absdiff", 1e-2)) {
                std::cerr << "Mismatch for "
                          << "mat"
                          << "\n";
                std::cout << mr_dists_ref << "\n";
                std::cout << mr_dists << "\n";
                std::exit(EXIT_FAILURE);
            }
        }

        if (print) {
            double speedup = ref_time / ms;
            std::cout << std::right << "|"
                      << std::setw(7) << n_points << " | "
                      << std::setw(5) << dim << " | "
                      << std::setw(16) << label << " | "
                      << std::setw(11) << std::fixed << std::setprecision(3) << ms << " ms | "
                      << std::setw(7) << std::fixed << std::setprecision(3) << speedup << " |"
                      << "\n";
        }
    };

    run(version_kdtree, "KDTree", true);
    // run(version_covertree, "CoverTree");
    run(version_scalar, "Scalar");
    run(version_scalar_openmp, "Scalar+OpenMP");
    // run(version_vectorized, "Vectorized");
    // run(version_vectorized_openmp, "Vectorized+OpenMP");

    if (print) {
        std::cout << std::right << "|"
                  << std::string(7, '-') << "-|-"
                  << std::string(5, '-') << "-|-"
                  << std::string(16, '-') << "-|-"
                  << std::string(11 + 3, '-') << "-|-"
                  << std::string(7, '-') << "-|"
                  << "\n";
    }
}

int main() {
    arma::arma_rng::set_seed(42);

    std::vector<int> sizes = {100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000};
    std::vector<int> dims = {1, 2, 3, 4, 5, 10, 20, 50, 100, 200, 500, 1000};  //, 2000, 5000, 10000};
    int k = 5;

    std::cout << std::right << "|"
              << std::setw(7) << "n"
              << " | "
              << std::setw(5) << "dim"
              << " | "
              << std::setw(16) << "Version"
              << " | "
              << std::setw(11 + 3) << "Time"
              << " | "
              << std::setw(7) << "Speedup"
              << " |"
              << "\n";
    std::cout << std::string(1 + 7 + 3 + 5 + 3 + 16 + 3 + 9 + 3 + 3 + 6 + 2, '-') << "\n";

    benchmark(10, 6, k, false);
    benchmark(20, 4, k, false);
    benchmark(15, 3, k, false);
    benchmark(10, 2, k, false);
    benchmark(17, 3, k, false);

    for (int n : sizes) {
        for (int d : dims) {
            benchmark(n, d, k);
        }
    }

    return 0;
}
