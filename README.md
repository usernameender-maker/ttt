# IEVF research prototype

This repository contains a small, standard-library-only prototype: a 16-bit
state codec, canonical JSON serialization, content-addressed evidence records,
a hash-linked JSONL audit ledger, and fail-closed fault-tolerance primitives.
It is **not** the complete IEVF Adaptive State Engine and is not certified,
production-ready, or suitable for safety-critical control.

## Current implementation

- `ievf.state`: encodes/decodes states in the range 0–65,535 as two big-endian bytes.
- `ievf.serialization`: canonical JSON and SHA-256 helpers.
- `ievf.evidence`: immutable evidence record structure, validation status, and digest.
- `ievf.audit`: sequence-checked hash-linked JSONL event ledger.
- `fault_tolerance`: quorum decision helper, bounded idempotent retry, checkpoint integrity, and restricted recovery gate.

The full v0.3.1 source, CLI, sensor adapters, tensor engine, distributed agents,
cryptographic identity, authenticated signatures, database, and external audit
anchoring are not present. Hash links detect inconsistency against trusted
expected values; they do not prevent rewriting/truncation or prove authenticity.
Failure-domain labels are caller assertions, not evidence of independence.

## Build and test

Requires Python 3.11 or later. Runtime dependencies are empty; `setuptools>=68`
is the build-system dependency.

```sh
python -m pip install --upgrade pip
python -m pip wheel --no-deps --wheel-dir wheelhouse .
python -m venv .venv
.venv/bin/python -m pip install --no-deps wheelhouse/*.whl
.venv/bin/python -m unittest discover -s tests -v
```

On Windows, invoke `.venv\\Scripts\\python.exe` instead of `.venv/bin/python`.
The GitHub Actions workflow runs the wheel install and tests in clean
Python 3.11, 3.12, and 3.13 environments.
