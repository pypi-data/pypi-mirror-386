

// std::vector<long long> euclidean_methods(std::vector<std::vector<double>> &vdata,
//                                    std::string mode,
//                                    long long k);


// std::vector<long long> euclidean_methods(std::vector<std::vector<double>> &data,
//                                    std::string mode,
//                                    long long k) {
//     // Other functions outside of our framework
//     if (mode == "euclidean_k_center") {
//         return euclidean_k_center(data, k);
//     } else if (mode == "euclidean_k_means") {
//         return euclidean_k_means(data, k);
//     } else if (mode == "agglomerative_single") {
//         return agglomerative_clustering(data, k, HCLUST_METHOD_SINGLE);
//     } else if (mode == "agglomerative_complete") {
//         return agglomerative_clustering(data, k, HCLUST_METHOD_COMPLETE);
//     } else if (mode == "agglomerative_average") {
//         return agglomerative_clustering(data, k, HCLUST_METHOD_AVERAGE);
//     } else if (mode == "agglomerative_median") {
//         return agglomerative_clustering(data, k, HCLUST_METHOD_MEDIAN);
//     } else {
//         std::cout << "mode '" << mode << "' not supported" << std::endl;
//         // throw std::runtime_error("mode '" + mode + "' not supported");
//         return std::vector<long long>(data.size());
//     }
// }