# IEVF research prototype

This repository contains a compact, standard-library-first research prototype for
fail-closed state validation, evidence tracking, auditability, and lightweight
language/word-game utilities. The current codebase is intentionally small and
explicitly does not claim to be a complete autonomous spatial or command engine.

The repository is organized around a minimal, dependency-light Python core and an
optional native acceleration path built with CMake and pybind11.

## Current implementation

The active package and utility modules are:

- `src/ievf/state.py`: 16-bit state encoding/decoding helpers
- `src/ievf/serialization.py`: canonical JSON and SHA-256 helper methods
- `src/ievf/evidence.py`: immutable evidence record structure and validation
- `src/ievf/audit.py`: hash-linked JSONL audit ledger with sequence checks
- `src/ievf/lifecycle.py`: lifecycle and checkpoint validation helpers
- `src/ievf/wordgame.py`: deterministic word scoring and 1-character ladder validation
- `src/ievf/phrase_communication.py`: explicit phrase-template matcher with slot extraction
- `src/ievf/native_wrapper.py`: optional native extension import and fallback wrapper
- `src/fault_tolerance.py`: quorum gates, bounded retry, checkpoint integrity, and guarded recovery logic

The native extension is built from:

- `native/CMakeLists.txt`
- `native/contraction.cpp`

The project also includes:

- `build_native.py`: optional CMake-backed native build and import validation
- `pyproject.toml`: build metadata and optional native dependency configuration
- `.github/workflows/native.yml`: native build validation workflow
- `.github/workflows/tests.yml`: cross-version Python test workflow

## Design goals

This repository emphasizes:

- deterministic validation over speculative heuristics
- fail-closed behavior and explicit integrity checks
- minimal runtime dependencies
- optional native acceleration without forcing native compilation for base users
- small, testable modules that can be extended incrementally

It is intentionally not a general-purpose autonomous control framework, language
model, or full spacecraft navigation system.

## Base installation

The base project does not require a heavy runtime stack.

```bash
python -m pip install -U pip
python -m pip install -e .
```

Base dependencies are intentionally minimal. The package is designed to stay
usable without the optional native extension.

## Optional native acceleration

The native acceleration path is optional and is intended for environments that
have a C++17 compiler and OpenMP support.

Install the optional native dependencies:

```bash
python -m pip install -e '.[native]'
```

Then build the extension:

```bash
python build_native.py
```

This uses CMake to configure and compile the optional native module, then verifies
that the importable extension loads successfully.

## Running tests

The repository uses the Python standard `unittest` discovery flow.

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

To run the workflow-like native validation directly:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
```

## Repository structure

```text
.
├── .github/
│   └── workflows/
│       ├── native.yml
│       └── tests.yml
├── LICENSE
├── README.md
├── build_native.py
├── native/
│   ├── CMakeLists.txt
│   └── contraction.cpp
├── pyproject.toml
├── src/
│   ├── fault_tolerance.py
│   └── ievf/
│       ├── __init__.py
│       ├── audit.py
│       ├── evidence.py
│       ├── lifecycle.py
│       ├── native_wrapper.py
│       ├── phrase_communication.py
│       ├── serialization.py
│       ├── state.py
│       └── wordgame.py
└── tests/
```

## Notes on scope and maturity

This project is a prototype and research scaffold. It is suitable for:

- state encoding experiments
- deterministic validation flows
- audit and evidence-chain reasoning
- explicit phrase and command matching
- optional native extension validation

It is not a complete productized system for:

- high-assurance autonomous control
- full navigation autonomy
- production-grade cryptographic attestation
- unrestricted language understanding
- general-purpose environmental world models

## Optional native dependency summary

The optional native path requires:

- Python 3.11+
- CMake 3.18+
- C++17 compiler
- OpenMP-enabled toolchain
- `numpy>=1.26,<3`
- `pybind11>=2.12,<4`

## License

Licensed under the AGPL-3.0-or-later terms described in `LICENSE`.
