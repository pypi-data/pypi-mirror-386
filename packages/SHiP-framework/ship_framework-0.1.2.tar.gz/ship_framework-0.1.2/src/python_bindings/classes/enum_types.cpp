#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <framework/partitioning/available_partitionings.hpp>
#include <framework/tree_construction/available_trees.hpp>
#include <pch.hpp>

namespace py = pybind11;


inline void bind_UltrametricTreeTypes(py::module_ &m) {
    py::module ultrametric_tree_submodule = m.def_submodule("ultrametric_tree");

    ultrametric_tree_submodule.doc() = R"pbdoc(
        This submodule contains all available ultrametric tree types. 
        There are different ways how to select and use an ultrametric tree type.


        **Usage Example**

        1. **Import a specific ultrametric tree type directly from the submodule:**

        .. code-block:: python

            from SHiP import SHiP
            from SHiP.ultrametric_tree import <UltrametricTreeType>

            ship = SHiP(data=my_data, treeType=<UltrametricTreeType>)

        2. **Use the ``UltrametricTreeType`` enum to list and access all available tree types:**

        .. code-block:: python

            from SHiP import SHiP
            from SHiP.ultrametric_tree import UltrametricTreeType

            for tree_type in UltrametricTreeType:
                print(tree_type)

            ship = SHiP(data=my_data, treeType=UltrametricTreeType.<UltrametricTreeType>)

        3. **Specify the tree type as a string (ensure it matches an available ultrametric tree type):**

        .. code-block:: python

            from SHiP import SHiP

            ship = SHiP(data=my_data, treeType="<UltrametricTreeType>")
    )pbdoc";

    // UltrametricTreeTypes
    auto ultrametricTreeTypes = py::enum_<UltrametricTreeType>(ultrametric_tree_submodule, "UltrametricTreeType", R"pbdoc(
        Enum of available ultrametric tree types.

        Can be used to iterate over or to select a tree type when initializing `SHiP`.

        **Example:**

        .. code-block:: python

            from SHiP.ultrametric_tree import UltrametricTreeType

            for tree_type in UltrametricTreeType:
                print(tree_type)

            ship = SHiP(data=my_data, treeType=UltrametricTreeType.<UltrametricTreeType>)
    )pbdoc");
    for (auto const &[type, name] : ultrametricTreeTypeStrings) {
        ultrametricTreeTypes.value(name.data(), type);
    }
    ultrametricTreeTypes.export_values();

    ultrametricTreeTypes.def(py::init([](const std::string &name) {
        return string_to_ultrametric_tree_type(name);
    }));
    py::implicitly_convertible<std::string, UltrametricTreeType>();

    // Provide a list of available UltrametricTreeTypes
    ultrametric_tree_submodule.attr("AVAILABLE_ULTRAMETRIC_TREE_TYPES") = py::cast(get_available_ultrametric_tree_types());
    ultrametric_tree_submodule.attr("AVAILABLE_ULTRAMETRIC_TREE_TYPES_AS_STRINGS") = py::cast(get_available_ultrametric_tree_types_as_strings());

    // Provide converter functions
    ultrametric_tree_submodule.def("stringToUltrametricTreeType",
                                   string_to_ultrametric_tree_type,
                                   "Convert a string to a UltrametricTreeType enum.");
    ultrametric_tree_submodule.def("ultrametricTreeTypeToString",
                                   ultrametric_tree_type_to_string,
                                   "Convert a UltrametricTreeType enum to a string.");
}


inline void bind_PartitioningMethods(py::module_ &m) {
    py::module partitioning_submodule = m.def_submodule("partitioning");

    partitioning_submodule.doc() = R"pbdoc(
    This submodule contains all available partitioning methods.
    There are different ways how to select and use a partitioning method.


    **Usage Examples:**

    1. Import a specific partitioning method directly from the submodule:

    .. code-block:: python

        from SHiP import SHiP
        from SHiP.partitioning import <PartitioningMethod>

        ship = SHiP(data=my_data)
        labels = ship.fit_predict(partitioningMethod=<PartitioningMethod>)

    2. Alternatively, use the `PartitioningMethod` enum to list and access all available partitioning methods:

    .. code-block:: python

        from SHiP import SHiP
        from SHiP.partitioning import PartitioningMethod

        for partitioning_method in PartitioningMethod:
            print(partitioning_method)

        ship = SHiP(data=my_data)
        labels = ship.fit_predict(partitioningMethod=PartitioningMethod.<PartitioningMethod>)

    3. You can also specify the partitioning method as a string (ensure it matches an available method):

    .. code-block:: python

        from SHiP import SHiP

        ship = SHiP(data=my_data)
        labels = ship.fit_predict(partitioningMethod="<PartitioningMethod>")
    )pbdoc";

    // PartitioningMethods
    auto partitioningMethods = py::enum_<PartitioningMethod>(partitioning_submodule, "PartitioningMethod", R"pbdoc(
    Enum of available partitioning methods.

    Can be used to iterate over or to select a partitioning method for `SHiP`.

    **Example:**

    .. code-block:: python

        from SHiP.partitioning import PartitioningMethod

        for method in PartitioningMethod:
            print(method)

        ship = SHiP(data=my_data)
        labels = ship.fit_predict(partitioningMethod=PartitioningMethod.<Method>)
)pbdoc");

    for (auto const &[type, name] : partitioningMethodStrings) {
        partitioningMethods.value(name.data(), type);
    }
    partitioningMethods.export_values();

    partitioningMethods.def(py::init([](const std::string &name) {
        return string_to_partitioning_method(name);
    }));
    py::implicitly_convertible<std::string, PartitioningMethod>();

    // Provide a list of available PartitioningMethods
    partitioning_submodule.attr("AVAILABLE_PARTITIONING_METHODS") = py::cast(get_available_partitioning_methods());
    partitioning_submodule.attr("AVAILABLE_PARTITIONING_METHODS_AS_STRINGS") = py::cast(get_available_partitioning_methods_as_strings());

    // Provide converter functions
    partitioning_submodule.def("stringToPartitioningMethod",
                               &string_to_partitioning_method,
                               "Convert a string to a PartitioningMethod enum.");
    partitioning_submodule.def("partitioningMethodToString",
                               &partitioning_method_to_string,
                               "Convert a PartitioningMethod enum to a string.");
}


inline void bind_Logger(py::module_ &m) {
    ///// Logger Module /////
    py::module logger_submodule = m.def_submodule("logger");

    logger_submodule.doc() = R"pbdoc(
        **Logging Configuration:**

        1. Import and set the desired log level directly from the submodule:

        .. code-block:: python

            from SHiP.logger import setLogLevel, <LogLevel>

            setLogLevel(<LogLevel>)

        2. Alternatively, use the `LogLevel` enum to list and access available log levels:

        .. code-block:: python

            from SHiP.logger import setLogLevel, LogLevel

            for log_level in LogLevel:
                print(log_level)

            setLogLevel(LogLevel.<LogLevel>)

        3. You can also specify the log level as a string (ensure it matches an available log level):

        .. code-block:: python

            from SHiP.logger import setLogLevel

            setLogLevel("<LogLevel>")
    )pbdoc";

    // LoggerTypes
    auto logLevels = py::enum_<LogLevel>(logger_submodule, "LogLevel", R"pbdoc(
    Enum of available logging levels for SHiP.

    Used with `setLogLevel()` to configure verbosity.

    Example:

    .. code-block:: python

        from SHiP.logger import setLogLevel, LogLevel

        setLogLevel(LogLevel.Warning)
)pbdoc");
    for (auto const &[type, name] : logLevelStrings) {
        logLevels.value(name.data(), type);
    }
    logLevels.export_values();

    // Provide a list of available UltrametricTreeTypes
    logger_submodule.def("setLogLevel",
                         py::overload_cast<LogLevel>(&::setLogLevel),
                         "Set the log level using a LogLevel enum");
    logger_submodule.def(
        "setLogLevel",
        [](const std::string &lvl) {
            setLogLevel(const_cast<std::string &>(lvl));
        },
        "Set the log level using a string name");
}
