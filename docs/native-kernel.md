## Optional native matrix kernel

The project remains a standard-library-only Python package by default. An
optional C++17/OpenMP 2-D matrix-multiplication extension is available for
research and does not replace the pure-Python core. It is not a general
`numpy.tensordot` implementation and does not claim bitwise floating-point
identity with NumPy.

Install the optional Python requirements with `python -m pip install -e '.[native]'`.
CMake, a C++17 compiler with OpenMP, and Python development headers are system
build requirements. Then run:

```sh
python build_native.py
PYTHONPATH=src python -m unittest discover -s tests -p test_native_contract.py -v
```

The default package test workflow does not install optional NumPy/native build
requirements, so `test_native_contract.py` skips when either NumPy or the
compiled extension is unavailable. The dedicated native CI workflow installs
the dependencies, builds and import-checks the extension first, and therefore
runs the native tests rather than skipping them.

`ievf.native_wrapper.NativeCore(require_native=True)` refuses to fall back and
is used by the native tests. The default wrapper may use NumPy if the optional
extension is unavailable. The native kernel supports only two-dimensional
matrices with matching inner dimensions. It parallelizes independent output
elements while retaining a fixed summation order for each result; compiler
fast-math and host-specific instruction-set flags are intentionally omitted.

The native binary is emitted into `src/ievf` for local import and is a generated
build artifact. CI builds and tests it on Ubuntu and Windows; no machine-specific
binary is published as a trusted artifact.
