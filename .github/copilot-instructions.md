# Repository Guidelines for GitHub Copilot

## Core engineering philosophy
- Evidence-driven first: never guess performance metrics, memory footprints, or algorithmic complexity. Rely on benchmarks, profiling data, and schema validation.
- Strict correctness: any native acceleration (C++/OpenMP/AVX) must cross-validate against reference NumPy implementations. Fail fast on precision drift.
- Zero-bloat architecture: keep modules modular, lightweight, and self-contained. Avoid speculative dependencies or unverified abstractions.

## Coding standards
- C++ native core: ensure cache-blocking tile strategies, boundary safety, and explicit memory alignment. Avoid undefined behavior.
- Python wrappers: maintain type annotations, strict docstrings, and robust exception handling.
- Testing and benchmarks: all performance changes must be backed by JSONL benchmarking logs and schema validation (`research-data/result.schema.json`).
- Keep benchmark scenarios bounded and deterministic. Preserve fixed seeds and explicit memory caps.

## Repository-specific rules
- The current repository is a research prototype for synthetic matrix-contraction and state-wall validation, not a production autonomous system.
- Do not invent “flight controller,” “swarm,” “telemetry mesh,” or similar production features unless the code and tests exist for them.
- Prefer transparent, reproducible benchmark definitions in `research-data/scenarios.json` over opaque or hidden performance tuning.
- If a benchmark result is not logged with environment metadata, treat it as untrustworthy evidence.

## Required validation patterns
- Native performance work must include a path that compares output against NumPy reference values with a documented tolerance.
- Small deterministic cases come before larger cases. Increases in matrix dimensions must have explicit memory guards and a rationale.
- Benchmark outputs should be stored in JSONL and validated against `research-data/result.schema.json` when possible.

## Scope guardrails
- Keep the hot path limited to actual code and tests in the repository.
- Avoid speculative changes that are not connected to metadata, tests, or benchmarked evidence.
- Favor additive, well-contained changes over broad refactors.
