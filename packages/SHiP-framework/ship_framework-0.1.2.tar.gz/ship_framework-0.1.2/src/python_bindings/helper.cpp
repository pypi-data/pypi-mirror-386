#include "helper.hpp"

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <pch.hpp>

namespace py = pybind11;


// Helper: takes any array-like, forces it to a C‑contiguous float64 2D array,
// then converts to std::vector<std::vector<double>>.
std::vector<std::vector<double>> pyarray_to_vector2D(py::object arr_obj) {
    // 1) import NumPy and make C‑contiguous float64 copy if needed
    py::module_ np = py::module_::import("numpy");

    // Use numpy.ascontiguousarray(arr_obj, dtype=float64) to handle sparse/masked/etc.
    py::array_t<double, py::array::c_style | py::array::forcecast>
        arr = np.attr("ascontiguousarray")(arr_obj, np.attr("float64"))
                  .cast<py::array_t<double, py::array::c_style | py::array::forcecast>>();
    // Now arr is guaranteed 2D, C‑style, double

    // 2) check dimensions
    if (arr.ndim() != 2) {
        LOG_ERROR << "`data` must be 2-dimensional.";
        throw std::invalid_argument(
            "Input must be 2-dimensional after conversion: got ndim=" +
            std::to_string(arr.ndim()));
    }

    // 3) get raw pointer and shape
    py::buffer_info info = arr.request();
    auto ptr = static_cast<double *>(info.ptr);
    unsigned long long n_rows = info.shape[0];
    unsigned long long n_cols = info.shape[1];

    // 4) copy each row
    std::vector<std::vector<double>> result(n_rows, std::vector<double>(n_cols));
    for (unsigned long long i = 0; i < n_rows; ++i) {
        std::memcpy(result[i].data(),
                    ptr + i * n_cols,
                    n_cols * sizeof(double));
    }
    return result;
}


std::unordered_map<std::string, std::string> py_dict_to_string_map(const py::dict &d) {
    std::unordered_map<std::string, std::string> m;
    for (auto item : d) {
        // Ensure both key and value are castable to string
        std::string key = py::str(item.first).cast<std::string>();
        std::string val = py::str(item.second).cast<std::string>();
        m.emplace(std::move(key), std::move(val));
    }
    return m;
}
