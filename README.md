# IEVF research prototype

This repository contains a compact, dependency-light Python research prototype for
fail-closed state validation, evidence tracking, auditability, and deterministic
phrase/word-game utilities. It is not a production autonomous navigation system.

## Current components

- `src/ievf/state.py`: 16-bit state encoding and decoding
- `src/ievf/serialization.py`: canonical JSON and SHA-256 helpers
- `src/ievf/evidence.py`: immutable evidence records and validation
- `src/ievf/audit.py`: hash-linked JSONL audit ledger
- `src/ievf/lifecycle.py`: lifecycle and checkpoint validation
- `src/ievf/wordgame.py`: deterministic word scoring and word-ladder checks
- `src/ievf/phrase_communication.py`: explicit phrase templates and slot extraction
- `src/ievf/native_wrapper.py`: optional native matrix kernel with explicit fallback
- `src/fault_tolerance.py`: quorum, retry, checkpoint, and guarded recovery primitives
- `src/ievf/batch_runner.py`: memory-bounded synthetic matrix-contraction benchmark batches

The optional native extension is defined in `native/CMakeLists.txt` and
`native/contraction.cpp`, and can be built with `python build_native.py`.

## Dependencies and installation

The base package targets Python 3.11+ and has no mandatory runtime dependencies.

```bash
python -m pip install -e .
```

The native extension and benchmark require NumPy; compiling the extension also
requires pybind11, CMake, a C++17 compiler, and an OpenMP-capable toolchain:

```bash
python -m pip install -e '.[native]'
python build_native.py
```

For benchmark-only use without compiling the extension:

```bash
python -m pip install numpy
```

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Native kernel tests are skipped when the optional extension is not built. Native
CI builds the extension first and runs those tests in strict native mode.

## Synthetic contraction benchmark

`BatchRunner` runs deterministic, synthetic matrix multiplication cases, checks
estimated allocation against a per-case memory limit, optionally compares output
to NumPy, and appends JSONL measurements (backend, dimensions, timing, GFLOP/s,
contraction count, and error) for later comparison. It does not simulate a mesh,
Kalman filter, navigation, or real telemetry.

```python
from ievf.batch_runner import BatchRunner, BatchScenario

scenarios = [
    BatchScenario("baseline", m=128, k=128, n=128, seed=7),
    BatchScenario("larger", m=256, k=256, n=128, seed=8),
]
results = BatchRunner("benchmark-results/run.jsonl").run_batch(scenarios)
for result in results:
    print(result.scenario, result.backend, result.mean_ms, result.gflops_at_min)
```

The default memory cap is 256 MiB per scenario. Verification is limited to
individual dimensions up to 2048 and is included in the allocation estimate.

## Scope

The repository currently does not implement AETHER-MESH, quantum telemetry,
GNSS/WGS-84 conversion, a Kalman filter, or production navigation. Any future
multi-agent work should be clearly labeled as synthetic research simulation until
validated independently.

## License

Licensed under AGPL-3.0-or-later; see `LICENSE`.
