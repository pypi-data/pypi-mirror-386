#include <framework/SHiP.hpp>
#include <framework/tree_structure.hpp>
#include <pch.hpp>


long long getMedianK(std::vector<long long>& vec) {
    std::sort(vec.begin(), vec.end());
    unsigned long long n = vec.size();
    if (n % 2 != 0) {
        // If odd, return the middle element
        return vec[n / 2];
    } else {
        // If even, return the average of the two middle elements
        return static_cast<long long>(std::round((double)(vec[n / 2 - 1] + vec[n / 2]) / 2.0));
    }
}

long long getMeanK(std::vector<long long>& vec) {
    if (vec.empty())
        return 0;  // Handle empty vector case
    double sum = std::accumulate(vec.begin(), vec.end(), 0.0);
    return static_cast<long long>(std::round(sum / (double)vec.size()));
}


// Extract labels given the `PartitioningMethod`
std::vector<long long> SHiP::partitioning() {
    switch (this->partitioning_method) {
        case PartitioningMethod::K: {
            long long k = get_config_value_in_range<long long>(this->config, "k", 2, 1, this->data.size(), true);
            return this->get_tree(this->hierarchy)->kcenter_cut(k);
        }

        case PartitioningMethod::Elbow: {
            unsigned long long k = this->get_tree(this->hierarchy)->get_elbow_k();
            return this->get_tree(this->hierarchy)->kcenter_cut(k);
        }

        case PartitioningMethod::Threshold: {
            long long k = get_config_value_in_range<long long>(this->config, "k", 2, 1, this->data.size(), true);
            return this->get_tree(this->hierarchy)->threshold_cut(k);
        }

        case PartitioningMethod::ThresholdElbow: {
            return this->get_tree(this->hierarchy)->threshold_elbow_cut();
        }

        case PartitioningMethod::QCoverage: {
            long long k = get_config_value_in_range<long long>(this->config, "k", 2, 1, this->data.size(), true);
            long long min_cluster_size = get_config_value_in_range<long long>(this->config, "min_cluster_size", 5, 1, this->data.size());
            return this->get_tree(this->hierarchy)->threshold_q_coverage(k, min_cluster_size);
        }

        case PartitioningMethod::QCoverageElbow: {
            long long min_cluster_size = get_config_value_in_range<long long>(this->config, "min_cluster_size", 5, 1, this->data.size());
            return this->get_tree(this->hierarchy)->threshold_q_coverage(0, min_cluster_size, false, true);
        }

        case PartitioningMethod::QStem: {
            long long k = get_config_value_in_range<long long>(this->config, "k", 2, 1, this->data.size(), true);
            long long min_cluster_size = get_config_value_in_range<long long>(this->config, "min_cluster_size", 5, 1, this->data.size());
            return this->get_tree(this->hierarchy)->threshold_q_coverage(k, min_cluster_size, true, false);
        }

        case PartitioningMethod::QStemElbow: {
            long long min_cluster_size = get_config_value_in_range<long long>(this->config, "min_cluster_size", 5, 1, this->data.size());
            return this->get_tree(this->hierarchy)->threshold_q_coverage(0, min_cluster_size, true, true, true);
        }

        case PartitioningMethod::LcaNoiseElbow: {
            return this->get_tree(this->hierarchy)->get_lca_prune_solution();
        }

        case PartitioningMethod::LcaNoiseElbowNoTriangle: {
            return this->get_tree(this->hierarchy)->get_lca_prune_solution(false);
        }

        case PartitioningMethod::MedianOfElbows: {
            long long elbow_start_z = get_config_value_in_range<long long>(this->config, "elbow_start_z", 1, 0, this->data.size());
            long long elbow_end_z = get_config_value_in_range<long long>(this->config, "elbow_end_z", 5, 0, this->data.size());

            if (elbow_end_z < elbow_start_z) {
                LOG_ERROR << "'elbow_end_z' should be greater than or equal to 'elbow_start_z'";
                throw std::invalid_argument("'elbow_end_z' should be greater than or equal to 'elbow_start_z'");
            }

            std::vector<long long> vec;
            for (long long z = elbow_start_z; z <= elbow_end_z; z++) {
                vec.push_back(this->get_tree(z)->get_elbow_k());
            }

            long long median = getMedianK(vec);
            return this->get_tree(this->hierarchy)->threshold_cut(median);
        }

        case PartitioningMethod::MeanOfElbows: {
            long long elbow_start_z = get_config_value_in_range<long long>(this->config, "elbow_start_z", 1, 0, this->data.size());
            long long elbow_end_z = get_config_value_in_range<long long>(this->config, "elbow_end_z", 5, 0, this->data.size());

            if (elbow_end_z < elbow_start_z) {
                LOG_ERROR << "'elbow_end_z' should be greater than or equal to 'elbow_start_z'";
                throw std::invalid_argument("'elbow_end_z' should be greater than or equal to 'elbow_start_z'");
            }

            std::vector<long long> vec;
            for (long long z = elbow_start_z; z <= elbow_end_z; z++) {
                vec.push_back(this->get_tree(z)->get_elbow_k());
            }

            long long mean = getMeanK(vec);
            return this->get_tree(this->hierarchy)->threshold_cut(mean);
        }

        case PartitioningMethod::Stability: {
            long long min_cluster_size = get_config_value_in_range<long long>(this->config, "min_cluster_size", 5, 1, this->data.size());
            return this->get_tree(this->hierarchy)->stability_cut(min_cluster_size);
        }

        case PartitioningMethod::NormalizedStability: {
            long long min_cluster_size = get_config_value_in_range<long long>(this->config, "min_cluster_size", 5, 1, this->data.size());
            return this->get_tree(this->hierarchy)->normalized_stability_cut(min_cluster_size);
        }

            // case PartitioningMethod::PythonFunction: {
            //     py::function partitioning_function = py::reinterpret_borrow<py::function>(py::module::import("partitioning_functions").attr(function.c_str()));
            //     SHiP ship(min_points, min_cluster_size, partitioning_function);
            //     ship.fit(this->data);
            //     this->labels_.push_back(ship.labels_);
            //     return this->get_tree(this->hierarchy)->
            // }

            // SHiP(long long min_points,
            //     long long min_cluster_size,
            //     double (*obj_func)(std::shared_ptr<Node>));
            // SHiP(long long min_points,
            //     long long min_cluster_size,
            //     py::function objective);


            // py::dict bottom_up_cluster(std::shared_ptr<Node> tree);  // This signature should be changed depending on how the actual assigning and maintenance of current clusters will be.


            // Python objective function
            // py::function python_objective;
            // double (*python_partitioning_function)(std::shared_ptr<Node>);


        default: {
            LOG_ERROR << "Selected PartitioningMethod '" << partitioning_method_to_string(this->partitioning_method) << "' is invalid!";
            throw std::invalid_argument("Invalid PartitioningMethod");
        }
    }
}
