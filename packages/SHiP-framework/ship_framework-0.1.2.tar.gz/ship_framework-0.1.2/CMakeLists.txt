cmake_minimum_required(VERSION 3.17)
project(SHiP VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(PYBIND11_FINDPYTHON ON)


# Faster compile time
find_program(CCACHE_PROGRAM ccache)
if(CCACHE_PROGRAM)
    # Wrap *both* C and C++ compilers through ccache:
    set(CMAKE_C_COMPILER_LAUNCHER "${CCACHE_PROGRAM}")
    set(CMAKE_CXX_COMPILER_LAUNCHER "${CCACHE_PROGRAM}")
endif()

# Detect the number of processors and set CMAKE_BUILD_PARALLEL_LEVEL
if(NOT CMAKE_BUILD_PARALLEL_LEVEL)
    include(ProcessorCount)
    ProcessorCount(NUM_PROC)
    set(CMAKE_BUILD_PARALLEL_LEVEL ${NUM_PROC})
endif()
message(STATUS "Using ${CMAKE_BUILD_PARALLEL_LEVEL} threads for parallel build")

# Compiler flags (for Debug and Release builds)
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O0 -DDEBUG -g -fvisibility=default -fno-omit-frame-pointer -fsanitize=address -fsanitize=undefined -static-libasan -Wall -Wextra -Wconversion -Wfloat-conversion") # -ftime-report
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O0 -DDEBUG -g -fvisibility=default -fno-omit-frame-pointer -fsanitize=address -static-libasan -Wall -Wextra -Wconversion -Wfloat-conversion")
elseif(MSVC)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /O2 /W3")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} /O2 /W3")
else()
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -pthread -march=native -funroll-loops -Wall -Wextra -Wconversion -Wfloat-conversion")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O3 -pthread -march=native -funroll-loops -Wall -Wextra -Wconversion -Wfloat-conversion")
endif()

# Ensure all code is compiled with -fPIC for shared library support
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find Python version for which to install the the python module
set(Python3_FIND_STRATEGY LOCATION)



##### Source Code Compilation #####

# Add all the static libraries
add_library(${PROJECT_NAME}_library STATIC
    # Helper
    src/helper/logger.cpp

    # SHiP Framework
    src/framework/SHiP.cpp
    src/framework/print_functions.cpp
    src/framework/tree_structure.cpp
    src/framework/tree_structure_json.cpp

    # Tree Constructions
    src/framework/tree_construction/tree_construction.cpp
    src/framework/tree_construction/available_trees.cpp
    src/framework/tree_construction/ultrametric_tree_structure.cpp
    src/framework/tree_construction/ultrametric_tree_structure_json.cpp
    src/framework/tree_construction/adapter/DCTree_adapter.cpp
    src/framework/tree_construction/adapter/HST_adapter.cpp
    src/framework/tree_construction/adapter/mlpack_trees_adapter.cpp
    src/framework/tree_construction/adapter/parse_json_to_tree.cpp
    src/framework/tree_construction/DCTree/dc_dist_computation.cpp
    src/framework/tree_construction/HST/HST_opt.cpp
    src/framework/tree_construction/HST/global.cpp

    # Hierarchy
    src/framework/hierarchy/hierarchy.cpp

    # Partitioning
    src/framework/partitioning/available_partitionings.cpp
    src/framework/partitioning/SHiP_partitioning.cpp
    src/framework/partitioning/tree_partitioning.cpp
    src/framework/partitioning/elbow_methods.cpp
)

# Find all the neccessary packages
find_package(mlpack REQUIRED)
find_package(Armadillo REQUIRED)
find_package(HDF5 QUIET)
find_package(cnpy REQUIRED)
find_package(fmt REQUIRED)
find_package(simdjson REQUIRED)
find_package(pybind11 CONFIG REQUIRED)
find_package(Python3 COMPONENTS Interpreter Development.Module REQUIRED)
find_package(OpenMP REQUIRED)
# Math libraries
# find_package(Eigen3 REQUIRED)
# find_package(blaze REQUIRED)
# find_package(OpenBLAS REQUIRED)
# find_package(xtensor REQUIRED)


# Link necessary libraries to the static library
target_link_libraries(${PROJECT_NAME}_library
    mlpack::mlpack
    Armadillo::Armadillo
    HDF5::HDF5
    cnpy::cnpy
    fmt::fmt
    simdjson::simdjson
    # OpenMP::OpenMP
    ## Math libraries ##
    # Eigen3::Eigen
    # blaze::blaze
    # OpenBLAS::OpenBLAS
    # xtensor
)

# Precompile headers for faster recompilation
target_precompile_headers(${PROJECT_NAME}_library PRIVATE
    src/pch.hpp
)

# Include necessary directories
message(STATUS "Python3 include dirs: ${Python3_INCLUDE_DIRS}")
target_include_directories(${PROJECT_NAME}_library PUBLIC
    src
    ${Python3_INCLUDE_DIRS}
)

# Link necessary directories
message(STATUS "Python3 library dirs: ${Python3_LIBRARY_DIRS}")
target_link_directories(${PROJECT_NAME}_library PRIVATE
    ${Python3_LIBRARY_DIRS}
)


# Add executable for main program
add_executable(${PROJECT_NAME}_exec src/cmain.cpp)
target_link_libraries(${PROJECT_NAME}_exec PRIVATE
    ${PROJECT_NAME}_library
)

# add_executable(speed_comparison src/benchmarks/vector_add_benchmark.cpp)
# target_link_libraries(speed_comparison PRIVATE
#     ${PROJECT_NAME}_library
# )

# add_executable(knn_benchmark src/benchmarks/mutual_reachability_benchmark.cpp src/benchmarks/_dist_computations.cpp)
# target_link_libraries(knn_benchmark PRIVATE
#     ${PROJECT_NAME}_library
# )


# Python bindings via pybind11
pybind11_add_module(${PROJECT_NAME} MODULE
    src/python_bindings/helper.cpp
    src/python_bindings/SHiP_module.cpp
    src/python_bindings/classes/enum_types.cpp
    src/python_bindings/classes/SHiP.cpp
    src/python_bindings/classes/tree_structure.cpp
)
target_link_libraries(${PROJECT_NAME} PRIVATE
    ${PROJECT_NAME}_library
    pybind11::module
    ${Python3_LIBRARIES}
)


# # Use stubgen to create .pyi for statement completion
# message(STATUS "Use stubgen to create .pyi for statement completion")
# add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
#     COMMAND stubgen -m ${PROJECT_NAME} -p ${PROJECT_NAME} -o .
#     COMMAND ls .
#     WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
#     COMMENT "Use stubgen to create .pyi for statement completion"
# )


##### Install Python Module #####
# Do not install Python module with cmake if it gets installed with pip:
option(INSTALL_PYTHON_MODULE "Enable Python module installation" FALSE)

if(INSTALL_PYTHON_MODULE)
    # For installing with cmake extract the current python version and install there. Not recommended!
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" -c "from distutils import sysconfig as sc; print(sc.get_python_lib(plat_specific=True))"
        OUTPUT_VARIABLE PYTHON_SITE
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    if(NOT PYTHON_SITE)
        message(FATAL_ERROR "Failed to determine Python site packages installation directory.")
    endif()

    message(STATUS "Installing Python module to ${PYTHON_SITE}")
    install(TARGETS ${PROJECT_NAME}
        LIBRARY DESTINATION "${PYTHON_SITE}/"
        RUNTIME DESTINATION "${PYTHON_SITE}/"
    )

    # Output final status messages
    message(STATUS "${PROJECT_NAME} library and Python module configured successfully.")

else()
    # pip will automatically find the correct Python path and install it. Recommended!
    install(TARGETS ${PROJECT_NAME} DESTINATION .)
endif()
