#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <cstdint>
#include <stdexcept>

namespace py = pybind11;

namespace {
using FloatArray = py::array_t<double, py::array::c_style | py::array::forcecast>;

py::array_t<double> contract_matrices(const FloatArray& a, const FloatArray& b) {
    if (a.ndim() != 2 || b.ndim() != 2) {
        throw std::invalid_argument("contract_matrices accepts only 2-D arrays");
    }
    const py::ssize_t m = a.shape(0);
    const py::ssize_t k = a.shape(1);
    const py::ssize_t b_k = b.shape(0);
    const py::ssize_t n = b.shape(1);
    if (k != b_k) {
        throw std::invalid_argument("inner matrix dimensions must match");
    }

    py::array_t<double> output({m, n});
    const double* lhs = a.data();
    const double* rhs = b.data();
    double* out = output.mutable_data();

    // Parallelize independent outputs; each dot product keeps fixed summation order.
    {
        py::gil_scoped_release release;
        const std::int64_t rows = static_cast<std::int64_t>(m);
        const std::int64_t cols = static_cast<std::int64_t>(n);
        const std::int64_t inner = static_cast<std::int64_t>(k);
        #pragma omp parallel for collapse(2) schedule(static)
        for (std::int64_t i = 0; i < rows; ++i) {
            for (std::int64_t j = 0; j < cols; ++j) {
                double sum = 0.0;
                for (std::int64_t q = 0; q < inner; ++q) {
                    sum += lhs[i * inner + q] * rhs[q * cols + j];
                }
                out[i * cols + j] = sum;
            }
        }
    }
    return output;
}
}  // namespace

PYBIND11_MODULE(_tve1_native, module) {
    module.doc() = "Optional OpenMP 2-D matrix contraction for IEVF research";
    module.def("contract_matrices", &contract_matrices,
               py::arg("a"), py::arg("b"),
               "Compute 2-D matrix product; this is not general tensordot.");
}
