# python/CMakeLists.txt
cmake_minimum_required(VERSION 3.18)

project(roboflex_webcam_gst_ext)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)
# If you don't do this, then the pybind11_add_module will think it's
# standalone and will not link correctly.
set(PYBIND11_CPP_STANDARD -std=c++20)


# -------------------- 
# Resolve dependencies

find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module NumPy)
#find_package(Python REQUIRED COMPONENTS Interpreter Development NumPy)

include(FetchContent)

# download and build pybind11
FetchContent_Declare(pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11.git
    GIT_TAG        v2.11.1
)
FetchContent_MakeAvailable(pybind11)

# download and build xtensor_python
FetchContent_Declare(xtensor-python
    GIT_REPOSITORY https://github.com/xtensor-stack/xtensor-python.git
    GIT_TAG        0.29.0
)
FetchContent_MakeAvailable(xtensor-python)


# -------------------- 
# Define the library

pybind11_add_module(roboflex_webcam_gst_ext
    pybindings.cpp
)

target_link_libraries(roboflex_webcam_gst_ext PUBLIC 
    roboflex_webcam_gst
    xtensor-python
)

set_target_properties(roboflex_webcam_gst_ext PROPERTIES
    POSITION_INDEPENDENT_CODE ON
    BUILD_WITH_INSTALL_RPATH TRUE
    INSTALL_RPATH "$ORIGIN"
)
