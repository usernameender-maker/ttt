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

## Native kernel optimization roadmap

The native extension currently implements a general 2-D matrix product using a
straightforward `i,j,q` loop, OpenMP `collapse(2)` with static scheduling, and
NumPy-owned input/output buffers. Treat the following as experiments, not assumed
wins; compare against the existing kernel on the same shapes, seeds, compiler,
thread count, and machine.

1. **Establish correctness and performance baselines.** Record representative
   square, tall, wide, small, and non-contiguous-input cases. Check results against
   NumPy with tolerances, and report repeated timing summaries and backend details.
2. **Try a portable loop-order improvement first.** For row-major arrays, an
   `i,q,j` loop makes the right-hand matrix and output traversals contiguous; zero
   each output row before accumulation. Keep the existing implementation as a
   comparison until correctness and speed are demonstrated across shapes.
3. **Then evaluate cache tiling and packing.** Add configurable tile sizes only if
   profiling shows cache/reuse limits. Packing has allocation and copy costs, so
   measure end-to-end time, including packing, over small and large matrices.
4. **Compare OpenMP policies empirically.** Equal-sized output tiles are generally
   uniform work, so static scheduling is a sensible baseline. Test guided/dynamic
   scheduling only for measured imbalance; record thread counts and avoid assuming
   that a 65,536-cell board implies a 65,536-dimensional matrix contraction.
5. **Keep memory ownership portable.** The current buffers are managed by NumPy
   and pybind11. Do not replace them with raw `posix_memalign` allocations unless
   ownership, deallocation, Windows portability, and array lifetime are handled.
   Unaligned loads are not automatically slower on modern CPUs; add alignment or
   ISA-specific intrinsics only after profiling and with a portable fallback.
6. **Preserve numerical behavior.** Avoid fast-math or changing accumulation order
   without tolerance-based correctness tests. Include zero-sized dimensions,
   non-contiguous arrays, dtype conversion, and invalid shapes in the contract tests.

The proposed Joseph-form covariance update, Kalman filter, AETHER-MESH telemetry,
and SPSC ring buffer do not match current repository components and are not
optimization tasks for this codebase. Revisit them only if those components are
actually introduced with requirements and tests. The state-wall simulation is a
toy game and does not currently use the native matrix kernel.

## Repository review checklist

Use this checklist every time you review a repository and want to keep momentum.

### 1. Establish baseline and scope
- [ ] Confirm repository, branch, and review goal.
- [ ] Record the starting commit and current branch state.
- [ ] Read the README and recent changes to understand actual scope.
- [ ] Check the available test commands, workflows, and data sources.
- [ ] Capture a baseline benchmark or status snapshot before changes.

### 2. Pick one improvement category at a time
- [ ] Correctness and edge cases
- [ ] Test reliability and coverage
- [ ] Runtime performance
- [ ] Memory/resource use
- [ ] Security and dependency hygiene
- [ ] Documentation and discoverability
- [ ] Observability and reproducibility
- [ ] Maintainability and architecture

For the selected category:
- [ ] Define the metric or pass/fail criteria before editing.
- [ ] Change only one variable at a time.
- [ ] Keep the baseline record for comparison.
- [ ] Run the smallest relevant set of tests and benchmarks.
- [ ] Compare results and document regressions or uncertainty.

### 3. Decision rules
- [ ] Keep the change only when the metric improves without meaningful regressions.
- [ ] If the improvement is not demonstrated, revert or mark it inconclusive.
- [ ] Move to another category or hypothesis instead of forcing a weak improvement.
- [ ] Never claim success without recorded results and reproduction steps.

### 4. Save the work and continue
- [ ] Store results in a versioned or backed-up location.
- [ ] Record repository, branch, commit, date, environment, seed, and metric summary.
- [ ] Add a brief next action so the next review can continue without repeating discovery.
- [ ] Leave an update in the project log, issue, or review notes.

### Review record template

```text
Date:
Repository:
Branch / commit:
Review goal:
Category:
Baseline:
Hypothesis:
Change:
Commands / scenarios:
Results:
Regressions or limitations:
Decision: keep / revert / inconclusive
Next action:
Data location:
```

## Scope

The project does not implement a real swarm, Kalman filter, quantum telemetry,
GNSS conversion, or production navigation system. The state-wall simulation and
matrix benchmarks are synthetic research tools.

## License

AGPL-3.0-or-later; see `LICENSE`.

---
Last time this was done: 2026-11-17
Signature: GitHub Copilot Chat Assistant
