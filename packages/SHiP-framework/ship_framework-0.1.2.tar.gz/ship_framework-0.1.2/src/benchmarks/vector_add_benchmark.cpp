#include <immintrin.h>
#include <omp.h>

#include <algorithm>
#include <chrono>
#include <execution>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <numeric>
#include <string>
#include <thread>
#include <vector>

// Include math libraries
#define EIGEN_NO_DEBUG
#include <blaze/Math.h>
#include <cblas.h>
// #include <oneapi/tbb.h>
// #include <tbb/parallel_for.h>
#include <Eigen/Dense>
#include <armadillo>
#include <xtensor/xadapt.hpp>
#include <xtensor/xarray.hpp>
#include <xtensor/xio.hpp>
#include <xtensor/xview.hpp>


// Benchmark configurations
constexpr int RUNS = 1000;
const std::vector<size_t> TEST_SIZES = {1, 2, 3, 4, 5, 10, 50, 100, 500, 1000,
                                        5000, 10000, 50000, 100000, 500000, 1000000};

void print_header() {
    std::cout << std::setw(18) << std::left << "Method"
              << " | " << std::setw(8) << "Size"
              << " | " << std::setw(15) << "Time (ns)"
              << " | " << std::setw(8) << "Speedup"
              << " |\n";
    std::cout << std::string(60, '-') << "\n";
}
void print_result(const std::string& name, size_t size, double avg_time, double speedup) {
    std::cout << std::setw(18) << std::left << name
              << " | " << std::setw(8) << size << " | ";
    if (avg_time > 100000.0) {
        std::cout << std::scientific << std::setprecision(2);
    } else {
        std::cout << std::fixed << std::setprecision(3);
    }
    std::cout << std::setw(12) << avg_time << " ns";
    std::cout << " | " << std::right << std::setw(7) << std::fixed << std::setprecision(3) << speedup << "  |\n";
}

void scalar_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
    for (size_t i = 0; i < a.size(); ++i) {
        c[i] = a[i] + b[i];
    }
}

void avx2_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
    size_t i = 0;
    for (; i + 4 <= a.size(); i += 4) {
        __m256d va = _mm256_loadu_pd(&a[i]);
        __m256d vb = _mm256_loadu_pd(&b[i]);
        _mm256_storeu_pd(&c[i], _mm256_add_pd(va, vb));
    }
    for (; i < a.size(); ++i) {
        c[i] = a[i] + b[i];
    }
}

#ifdef __AVX512F__
void avx512_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
    size_t i = 0;
    for (; i + 8 <= a.size(); i += 8) {
        __m512d va = _mm512_loadu_pd(&a[i]);
        __m512d vb = _mm512_loadu_pd(&b[i]);
        _mm512_storeu_pd(&c[i], _mm512_add_pd(va, vb));
    }
    for (; i < a.size(); ++i) {
        c[i] = a[i] + b[i];
    }
}
#endif

void omp_scalar_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
#pragma omp parallel for schedule(static)
    for (size_t i = 0; i < a.size(); ++i) {
        c[i] = a[i] + b[i];
    }
}

void omp_avx2_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
#pragma omp parallel for schedule(static)
    for (size_t i = 0; i < a.size(); i += 4) {
        if (i + 4 <= a.size()) {
            __m256d va = _mm256_loadu_pd(&a[i]);
            __m256d vb = _mm256_loadu_pd(&b[i]);
            _mm256_storeu_pd(&c[i], _mm256_add_pd(va, vb));
        } else {
            for (; i < a.size(); ++i) c[i] = a[i] + b[i];
        }
    }
}

#ifdef __AVX512F__
void omp_avx512_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
#pragma omp parallel for schedule(static)
    for (size_t i = 0; i < a.size(); i += 8) {
        if (i + 8 <= a.size()) {
            __m512d va = _mm512_loadu_pd(&a[i]);
            __m512d vb = _mm512_loadu_pd(&b[i]);
            _mm512_storeu_pd(&c[i], _mm512_add_pd(va, vb));
        } else {
            for (; i < a.size(); ++i) c[i] = a[i] + b[i];
        }
    }
}
#endif

// void par_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
//     tbb::parallel_for(size_t(0), a.size(), [&](size_t i) {
//         c[i] = a[i] + b[i];
//     });
// }

// void par_avx2_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
//     constexpr size_t chunk_size = 4;
//     tbb::parallel_for(size_t(0), (a.size() + chunk_size - 1) / chunk_size, [&](size_t chunk_idx) {
//         size_t i = chunk_idx * chunk_size;
//         if (i + chunk_size <= a.size()) {
//             __m256d va = _mm256_loadu_pd(&a[i]);
//             __m256d vb = _mm256_loadu_pd(&b[i]);
//             _mm256_storeu_pd(&c[i], _mm256_add_pd(va, vb));
//         } else {
//             for (; i < a.size(); ++i) {
//                 c[i] = a[i] + b[i];
//             }
//         }
//     });
// }

// void par_avx512_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
//     constexpr size_t chunk_size = 8;
//     tbb::parallel_for(size_t(0), (a.size() + chunk_size - 1) / chunk_size, [&](size_t chunk_idx) {
//         size_t i = chunk_idx * chunk_size;
//         if (i + chunk_size <= a.size()) {
//             __m512d va = _mm512_loadu_pd(&a[i]);
//             __m512d vb = _mm512_loadu_pd(&b[i]);
//             _mm512_storeu_pd(&c[i], _mm512_add_pd(va, vb));
//         } else {
//             for (; i < a.size(); ++i) {
//                 c[i] = a[i] + b[i];
//             }
//         }
//     });
// }

void eigen_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
    Eigen::Map<const Eigen::VectorXd> ea(a.data(), a.size());
    Eigen::Map<const Eigen::VectorXd> eb(b.data(), b.size());
    Eigen::Map<Eigen::VectorXd> ec(c.data(), c.size());
    ec = ea + eb;
}

void arma_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
    arma::vec ea(const_cast<double*>(a.data()), a.size(), false, true);
    arma::vec eb(const_cast<double*>(b.data()), b.size(), false, true);
    arma::vec ec(c.data(), c.size(), false, true);
    ec = ea + eb;
}


void arma_add_par(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
    arma::vec ea(const_cast<double*>(a.data()), a.size(), false, true);
    arma::vec eb(const_cast<double*>(b.data()), b.size(), false, true);
    arma::vec ec(c.data(), c.size(), false, true);

    #pragma omp parallel for schedule(static)
    for (size_t i = 0; i < c.size(); ++i) {
        ec(i) = ea(i) + eb(i);
    }
}


void xtensor_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
    auto xa = xt::adapt(a, {a.size()});
    auto xb = xt::adapt(b, {b.size()});
    auto xc = xt::adapt(c, {c.size()});
    xc = xa + xb;
}

void blaze_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
    blaze::DynamicVector<double> va(a.size(), a.data());
    blaze::DynamicVector<double> vb(b.size(), b.data());
    blaze::DynamicVector<double> vc(c.size(), c.data());
    vc = va + vb;
}

void blas_add(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
    cblas_dcopy(a.size(), a.data(), 1, c.data(), 1);
    cblas_daxpy(a.size(), 1.0, b.data(), 1, c.data(), 1);
}

template <typename Func>
double benchmark(Func&& func, const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& c) {
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < RUNS; ++i) {
        func(a, b, c);
        asm volatile(""
                     :
                     : "r,m"(c.data())
                     : "memory");
    }
    auto end = std::chrono::high_resolution_clock::now();
    return std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count() / (double)RUNS;
}

int main() {
    std::cout << "Starting benchmark...\n";
    std::cout << "OpenBLAS config: " << openblas_get_config() << std::endl;
    std::cout << "OpenBLAS threads: " << openblas_get_num_threads() << std::endl;
    std::cout << "CPU supports: ";
#ifdef __AVX2__
    std::cout << "AVX2 ";
#endif
#ifdef __AVX512F__
    std::cout << "AVX-512 ";
#endif
    std::cout << "\n\n";

    Eigen::initParallel();
    Eigen::setNbThreads(std::thread::hardware_concurrency());

    print_header();

    for (size_t size : TEST_SIZES) {
        std::vector<double> a(size, 1.0), b(size, 2.0), c(size);

        double scalar_time = benchmark(scalar_add, a, b, c);
        print_result("Scalar", size, scalar_time, 1.0);

        double avx2_time = benchmark(avx2_add, a, b, c);
        print_result("AVX2", size, avx2_time, scalar_time / avx2_time);

#ifdef __AVX512F__
        double avx512_time = benchmark(avx512_add, a, b, c);
        print_result("AVX-512", size, avx512_time, scalar_time / avx512_time);
#endif

        double omp_time = benchmark(omp_scalar_add, a, b, c);
        print_result("OpenMP", size, omp_time, scalar_time / omp_time);

        double omp_avx2_time = benchmark(omp_avx2_add, a, b, c);
        print_result("OpenMP+AVX2", size, omp_avx2_time, scalar_time / omp_avx2_time);

#ifdef __AVX512F__
        double omp_avx512_time = benchmark(omp_avx512_add, a, b, c);
        print_result("OpenMP+AVX-512", size, omp_avx512_time, scalar_time / omp_avx512_time);
#endif

        // double par_time = benchmark(par_add, a, b, c);
        // print_result("std::par", size, par_time, scalar_time / par_time);

        // double par_avx2_time = benchmark(par_avx2_add, a, b, c);
        // print_result("std::par+AVX2", size, par_avx2_time, scalar_time / par_avx2_time);

        // double par_avx512_time = benchmark(par_avx512_add, a, b, c);
        // print_result("std::par+AVX-512", size, par_avx512_time, scalar_time / par_avx512_time);

        double eigen_time = benchmark(eigen_add, a, b, c);
        print_result("Eigen", size, eigen_time, scalar_time / eigen_time);

        double arma_time = benchmark(arma_add, a, b, c);
        print_result("Armadillo", size, arma_time, scalar_time / arma_time);

        double arma_par_time = benchmark(arma_add_par, a, b, c);
        print_result("Armadillo (OMP)", size, arma_par_time, scalar_time / arma_par_time);

        double xtensor_time = benchmark(xtensor_add, a, b, c);
        print_result("xtensor", size, xtensor_time, scalar_time / xtensor_time);

        double blaze_time = benchmark(blaze_add, a, b, c);
        print_result("Blaze", size, blaze_time, scalar_time / blaze_time);

        double blas_time = benchmark(blas_add, a, b, c);
        print_result("BLAS", size, blas_time, scalar_time / blas_time);

        std::cout << "\n";
    }
    return 0;
}
