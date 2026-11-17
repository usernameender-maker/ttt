# IEVF fault-tolerance primitives

This repository currently contains a small, standard-library-only Python
prototype for fail-closed validator quorum decisions, bounded retries for
caller-guaranteed idempotent operations, checkpoint integrity checks, and a
restricted recovery gate.

It is **not** the complete IEVF Adaptive State Engine and is not certified,
production-ready, or suitable for safety-critical control. Validator identity
and failure-domain labels are caller assertions; the module does not implement
cryptographic identity, distributed consensus, a hash-linked ledger, replay
protection, or authorization of external actions. See
[`docs/fault-tolerance.md`](docs/fault-tolerance.md) and
[`docs/research-execution-contract.md`](docs/research-execution-contract.md)
for scope and limitations.

## Install and test

Python 3.11 or later is required. There are no runtime dependencies.

```sh
python -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests -v
```

Alternatively, run tests directly from the source tree:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

The `ievf-state` CLI and the full IEVF v0.3.1 source package are not present
in this repository branch. No tests or package installation are claimed as
successful until executed in an environment and reported by CI.
