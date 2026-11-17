#!/usr/bin/env bash
set -euo pipefail

JSONL_OUTPUT="${1:-research-data/results/bounded-benchmark.jsonl}"
PYTHON_BIN="${PYTHON_BIN:-python}"

mkdir -p "$(dirname "$JSONL_OUTPUT")"

echo "=========================================================================="
echo "IEVF bounded benchmark runner"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "=========================================================================="

echo "[*] Environment details"
python - <<'PY'
import json
import os
import platform
import sys

try:
    import numpy as np
    numpy_version = np.__version__
except Exception:
    numpy_version = "unavailable"

print(json.dumps({
    "python_version": sys.version.split()[0],
    "numpy_version": numpy_version,
    "platform": platform.platform(),
    "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
    "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
    "mkl_num_threads": os.environ.get("MKL_NUM_THREADS"),
}, sort_keys=True))
PY

echo "[*] Allocated memory budget check"
if command -v free >/dev/null 2>&1; then
    free -h || true
fi

# Validate only a bounded, supported set of scenarios.
PYTHONPATH=src "$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path
from ievf.batch_runner import BatchRunner, BatchScenario

manifest = json.loads(Path('research-data/scenarios.json').read_text(encoding='utf-8'))
scenarios = [BatchScenario(**row) for row in manifest['scenarios']]
results = BatchRunner('research-data/results/bounded-benchmark.jsonl').run_batch(scenarios)
print(f"Finished {len(results)} scenarios")
PY

echo "=========================================================================="
echo "Benchmark results saved to: $JSONL_OUTPUT"
echo "=========================================================================="
