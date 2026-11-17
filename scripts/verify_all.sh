#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

JSONL_OUTPUT="${1:-research-data/results/bounded-benchmark.jsonl}"
PYTHON_BIN="${PYTHON_BIN:-python}"

mkdir -p "$(dirname "$JSONL_OUTPUT")"

echo "=========================================================================="
echo "IEVF master verification pipeline"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "=========================================================================="

echo "[*] Step 1: build native extension"
"$PYTHON_BIN" -m pip install --no-build-isolation -e '.[native]' >/tmp/ievf_pip_install.log 2>&1 || {
  echo "pip install failed; trying build_native.py fallback"
  "$PYTHON_BIN" build_native.py
}

echo "[*] Step 2: run small scenario validation tests"
PYTHONPATH=src "$PYTHON_BIN" -m unittest tests/test_scenarios.py -v

echo "[*] Step 3: run bounded benchmark scenarios"
PYTHONPATH=src "$PYTHON_BIN" run_benchmarks.sh "$JSONL_OUTPUT"

echo "=========================================================================="
echo "Verification pipeline completed successfully"
echo "Results recorded to: $JSONL_OUTPUT"
echo "=========================================================================="
