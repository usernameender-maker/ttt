# IEVF research prototype

This repository is a dependency-light Python research prototype for state encoding,
validation, evidence, auditability, phrase matching, and optional native matrix
contraction. It is not a production autonomous navigation system.

## Components

- `src/ievf/state.py`: 16-bit state encoding and decoding
- `src/ievf/serialization.py`, `evidence.py`, `audit.py`, `lifecycle.py`: canonical records, validation, audit chain, and lifecycle helpers
- `src/ievf/phrase_communication.py`: deterministic phrase templates and slot extraction
- `src/ievf/native_wrapper.py`: optional native matrix kernel with explicit fallback
- `src/ievf/batch_runner.py`: bounded matrix contraction benchmarks with JSONL records
- `src/ievf/statewall.py`: seeded synthetic Battleship-style search/evade game on a state wall (256x256 = 65,536 cells by default)

The state-wall game is a toy benchmark, not a flight controller. Asteroids and
ships are simulated locally; no real telemetry, hardware, or external system is
connected.

## Install and test

Base package (Python 3.11+):

```bash
python -m pip install -e .
PYTHONPATH=src python -m unittest discover -s tests -v
```

Optional NumPy/native tools:

```bash
python -m pip install -e '.[native]'
python build_native.py
```

## Persistent benchmark data

`StatewallSimulation.save_jsonl(path)` appends one JSON object per tick and never
silently overwrites existing records. Each record includes scenario, seed, board
size, ships alive, targets found/remaining, hazard count, collision events, scan
coverage, command success, and nearest threat distance. Keep benchmark outputs in
a versioned or backed-up results directory; source-control commits preserve code
and schemas, but generated data is not automatically committed.

The matrix benchmark also appends JSONL results (backend, dimensions, seed,
contraction count, estimated memory, timing, throughput, and NumPy comparison
error). Example:

```python
from ievf.batch_runner import BatchRunner, BatchScenario

cases = [BatchScenario("baseline", m=128, k=128, n=128, seed=7)]
results = BatchRunner("benchmark-results/matrix.jsonl").run_batch(cases)
```

## Improvement loop

For each category (correctness, performance, memory, coverage, hazard collisions,
and reproducibility): preserve the baseline record, change one factor at a time,
rerun with the same seeds, compare metrics, and keep a change only when the
relevant metric improves without regressions elsewhere. If it does not demonstrate
an improvement, revert it and select a different category or hypothesis. Benchmark
measurements are evidence, not guarantees; compare repeated runs and record the
runtime/backend environment when making performance claims.

## Scope

The project does not implement a real swarm, Kalman filter, quantum telemetry,
GNSS conversion, or production navigation system. The state-wall simulation and
matrix benchmarks are synthetic research tools.

## License

AGPL-3.0-or-later; see `LICENSE`.
