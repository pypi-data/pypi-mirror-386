#!/usr/bin/env bash
cd "$(dirname "$0")"

BUILD_TYPE="Release"   # "Release" or "Debug"
INSTALL_PYTHON_MODULE="True"   # Install Python Module with cmake, set to FALSE if installed with pip

if command -v ninja >/dev/null 2>&1; then
    export CMAKE_GENERATOR=Ninja
fi

rm -rf build/
conan install . -of=build --build=missing --settings=build_type=$BUILD_TYPE
cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=conan_toolchain.cmake -DCMAKE_BUILD_TYPE=$BUILD_TYPE -DINSTALL_PYTHON_MODULE=$INSTALL_PYTHON_MODULE
cmake --build . -j && cmake --install .
