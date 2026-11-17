# Dependency policy

## Current dependency inventory

- Runtime: Python standard library only (`>=3.11`).
- Build backend: `setuptools>=68` from the build-system requirement.
- Tests: standard-library `unittest`.
- Optional research dependencies: none currently declared or required.

Do not add NumPy, PyTorch, SciPy, cryptography, Pydantic, HTTP clients, or a database client speculatively. Add a dependency only when actual code imports it and the capability, version constraints, install group, security impact, and tests are documented. Keep research/ML dependencies optional and separate from the security-critical core.

The complete IEVF v0.3.1 source and adapters have not been recovered in this repository; this policy describes only code currently present.
