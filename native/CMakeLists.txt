cmake_minimum_required(VERSION 3.18)
project(ievf_native VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)
find_package(OpenMP REQUIRED COMPONENTS CXX)

pybind11_add_module(_tve1_native MODULE ${CMAKE_CURRENT_SOURCE_DIR}/contraction.cpp)
target_link_libraries(_tve1_native PRIVATE OpenMP::OpenMP_CXX)
target_compile_features(_tve1_native PRIVATE cxx_std_17)

# Portable optimization only; avoid fast-math and host-specific ISA flags.
if(MSVC)
    target_compile_options(_tve1_native PRIVATE /O2)
else()
    target_compile_options(_tve1_native PRIVATE -O3)
endif()

set(IEVF_PYTHON_OUTPUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../src/ievf" CACHE PATH
    "Directory where the importable IEVF extension is emitted")
set_target_properties(_tve1_native PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${IEVF_PYTHON_OUTPUT_DIR}"
    RUNTIME_OUTPUT_DIRECTORY "${IEVF_PYTHON_OUTPUT_DIR}"
)
foreach(config Debug Release RelWithDebInfo MinSizeRel)
    string(TOUPPER "${config}" config_upper)
    set_target_properties(_tve1_native PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY_${config_upper} "${IEVF_PYTHON_OUTPUT_DIR}"
        RUNTIME_OUTPUT_DIRECTORY_${config_upper} "${IEVF_PYTHON_OUTPUT_DIR}"
    )
endforeach()
