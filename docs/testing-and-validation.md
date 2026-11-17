# Testing and validation

The repository currently has standard-library unit tests for the 16-bit codec,
canonical JSON, evidence record validation, audit-ledger integrity, and local
fault-tolerance primitives.

Build and test the installed wheel in isolation:

```sh
python -m pip wheel --no-deps --wheel-dir wheelhouse .
python -m venv .venv
.venv/bin/python -m pip install --no-deps wheelhouse/*.whl
.venv/bin/python -m unittest discover -s tests -v
```

The test command intentionally does not set `PYTHONPATH`. The repository does
not yet test authenticated identity, signature verification, cross-process
concurrency, durable ledger recovery, remote replay protection, tensor
reproducibility, or external adapters. A passing unit suite would not establish
those properties or validate scientific claims.
