# Independent research data bank

This directory contains **reproducible benchmark scenario definitions and data schemas**, not measured results. No performance numbers in this repository should be treated as observations unless they were produced by an identified run and committed or archived with provenance.

## Contents

- `scenarios.json`: bounded, seeded matrix-contraction scenarios for `ievf.batch_runner.BatchRunner`.
- `scenario.schema.json`: JSON Schema for validating the scenario manifest.
- `result.schema.json`: JSON Schema for validating JSONL records emitted by the current `BatchRunner`.

## Run the scenarios

Install the optional NumPy/native requirements, build the extension, then run from the repository root:

```bash
python -m pip install -e '.[native]'
python build_native.py
PYTHONPATH=src python - <<'PY'
import json
from pathlib import Path
from ievf.batch_runner import BatchRunner, BatchScenario

manifest = json.loads(Path("research-data/scenarios.json").read_text(encoding="utf-8"))
scenarios = [BatchScenario(**row) for row in manifest["scenarios"]]
results = BatchRunner("research-data/results/candidate.jsonl").run_batch(scenarios)
print(f"Wrote {len(results)} records")
PY
```

The manifest intentionally keeps each case small and verifies results against NumPy. To compare the native and fallback paths, run a separate fallback batch by setting `require_native` to `false`; label and preserve the two result files separately. Do not compare results across different machines or thread settings as if they were controlled experiments.

## Research handling and provenance

- Preserve raw JSONL output; do not hand-edit or overwrite records. Use a new filename for each run.
- Archive the commit SHA, branch, command, UTC start time, OS/CPU, Python and NumPy versions, compiler/build flags, and thread environment with each run. Current records include Python, NumPy, platform, and common thread variables; attach remaining environment details in the run notes.
- Keep generated result files out of source control unless the research project intentionally publishes them. Review for size and sensitive environment information before sharing.
- Seeds reproduce input generation, not timing. Repeat whole runs and report variability; bootstrap intervals from a few adjacent timings are not a substitute for independent runs.
- Treat these as synthetic matrix workloads. They are not measurements of deployed systems or real-world performance.
- Check the result schema version before aggregating records. Preserve the original records when migrating schemas.

## Scenario design

The manifest includes small square, tall, wide, and tiny cases, each with a fixed seed, verification enabled, and a per-case allocation ceiling. Extend it only with explicit workload rationale and a conservative memory estimate. `BatchRunner` validates estimated allocations before constructing input arrays; that estimate is a guardrail, not a guarantee of process-wide memory availability.
