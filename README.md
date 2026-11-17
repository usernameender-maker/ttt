# TVE-1 / IEVF: Deterministic Tensor Contraction Framework

TVE-1 / IEVF is a Python project for bounded, reproducible matrix-contraction benchmark runs. Its current implementation provides a scenario/result model and a batch runner in `src/ievf/batch_runner.py`. The runner creates seeded `float64` inputs, enforces an estimated-memory limit, optionally checks outputs against NumPy, records timing and environment metadata, and appends JSONL results.

> **Implementation status:** The repository currently contains the batch runner, but does not yet contain the native contraction extension, `native_wrapper.py`, scenario catalog, result schema, test suite, or end-to-end verification script described by the planned architecture. The current CI builds the Python wheel and checks bounded-scenario validation; it does not claim to build or benchmark a native kernel.

## Install

The package declares its runtime dependency (`numpy`) in `pyproject.toml`. Install it from a source checkout with:

```bash
python -m pip install .
```

For local development and packaging checks:

```bash
python -m pip install -e ".[dev]"
python -m build --wheel
```

The `dev` extra contains build, pre-commit, and pytest tooling. Runtime requirements and development tools are intentionally separated so deployment environments do not install test and formatting packages unnecessarily. A deployment should install the wheel built from the intended source revision; the target deployment platform has not yet been specified, so no platform-specific container or cloud configuration is included.

## Current repository layout

| Path | Role |
| --- | --- |
| `src/ievf/batch_runner.py` | Bounded scenario definitions, input generation, timing, optional NumPy comparison, and JSONL result logging. |
| `pyproject.toml` | Package metadata, supported Python version, runtime dependencies, and development extras. |
| `.github/workflows/verify.yml` | Python matrix CI, package installation, wheel build, and scenario memory/dimension validation. |
| `.pre-commit-config.yaml` | Common whitespace, JSON/YAML, Python formatting, and C++ formatting hooks. |

## Current runner behavior

`BatchScenario` describes a matrix multiplication with dimensions `m`, `k`, and `n`, a seed, warmup and measured iteration counts, a verification setting, and a maximum estimated allocation. The runner generates contiguous `float64` arrays with `numpy.random.default_rng(seed)`. When verification is enabled, it compares the result with `A @ B` using `rtol=1e-10` and `atol=1e-12` and rejects non-finite outputs.

The allocation estimate is checked before arrays are created. Verification is limited to dimensions no larger than 2048. Each result records the shapes, seed, backend label, timing summary, estimated memory, throughput, maximum absolute error (when verified), timestamp, Python/NumPy/platform information, and selected thread environment variables.

The runner imports `NativeCore` from `src/ievf/native_wrapper.py`, which is not present in the repository at this time. Add that module (and the native extension or an explicitly supported fallback) before invoking `BatchRunner.run_batch`.

## Verification

GitHub Actions runs on pushes and pull requests targeting `main` for Python 3.10, 3.11, and 3.12. It installs the package with development dependencies, compiles Python sources, builds a wheel, and exercises the runner's scenario validation without allocating benchmark matrices or requiring a native extension.

For local formatting and basic repository checks, install pre-commit and run:

```bash
python -m pip install pre-commit
pre-commit run --all-files
```

## Planned architecture and hardening

The following are planned capabilities, not currently implemented repository features:

- A native C++ contraction kernel with documented OpenMP/vectorization behavior and a Python wrapper that validates dtype, shapes, and memory layout.
- A versioned scenario catalog with explicit seeds, workload families, dimensions, and tolerances.
- Numerical tests against a NumPy reference implementation.
- A result JSON Schema and validation command for every telemetry record.
- A full verification script that builds the extension, runs tests, executes bounded benchmarks, and validates emitted results.
- Optional hardware-counter telemetry and additional asymmetric, non-power-of-two, and boundary-size workloads.

Benchmark claims should identify the backend and environment and should only be reported after the exact source revision has passed numerical validation. Timing alone is not evidence of numerical correctness or native execution.
