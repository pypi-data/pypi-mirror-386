from conan import ConanFile


class SHiP_Framework(ConanFile):
    name = "SHiP"
    settings = "os", "compiler", "build_type", "arch"
    requires = (
        "mlpack/4.3.0",
        "armadillo/12.6.4",
        "hdf5/1.14.4.3",
        "pybind11/2.13.5",
        "cnpy/cci.20180601",
        "fmt/11.1.4",
        "simdjson/3.12.3",
        # "llvm-openmp/18.1.8",
        ## Math libraries ##
        # "onetbb/2022.0.0",
        # "eigen/3.4.0",
        # "xtensor/0.25.0",
        # "blaze/3.8.2",
        # "openblas/0.3.25",
    )

    # default_options = {
    #     "openblas/*:build_cblas": True
    # }

    generators = "CMakeToolchain", "CMakeDeps"
