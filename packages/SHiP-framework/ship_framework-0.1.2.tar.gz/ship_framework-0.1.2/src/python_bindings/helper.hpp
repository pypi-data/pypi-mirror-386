#pragma once

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;


std::vector<std::vector<double>> pyarray_to_vector2D(py::object arr_obj);
std::unordered_map<std::string, std::string> py_dict_to_string_map(const py::dict &d);
