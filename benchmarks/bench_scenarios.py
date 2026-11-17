#!/usr/bin/env python3
"""Execute deterministic benchmark scenarios against the available backend."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ievf.batch_runner import BatchRunner, BatchScenario


def load_scenarios(path: str | Path) -> list[BatchScenario]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    scenarios = []
    for item in payload["scenarios"]:
        scenarios.append(
            BatchScenario(
                name=item["name"],
                m=int(item["rows"]),
                k=int(item["cols_a"]),
                n=int(item["cols_b"]),
                warmup=int(item.get("warmup", 1)),
                iterations=int(item.get("iterations", 3)),
                seed=int(item["seed"]),
                verify=True,
                require_native=bool(item.get("require_native", False)),
                max_memory_bytes=int(item.get("max_memory_bytes", 256 * 1024 * 1024)),
            )
        )
    return scenarios


def run_benchmarks(scenario_path: str | Path, output_path: str | Path) -> list[dict]:
    runner = BatchRunner(output_path=output_path)
    results = runner.run_batch(load_scenarios(scenario_path))
    return [result.__dict__ for result in results]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run deterministic contraction scenarios.")
    parser.add_argument("scenario_path", type=str, help="JSON scenario catalog path")
    parser.add_argument("--output", type=str, default="research-data/results/bounded-benchmark.jsonl")
    args = parser.parse_args()

    results = run_benchmarks(args.scenario_path, args.output)
    print(f"Completed {len(results)} scenario(s).")
