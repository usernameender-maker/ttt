#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python -m compileall -q src
PYTHONPATH=src python -m unittest -q tests.test_scenarios

if [[ $# -gt 0 ]]; then
  PYTHONPATH=src python scripts/validate_results.py "$1"
fi
