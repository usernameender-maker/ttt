"""Reproducible, memory-bounded matrix-contraction benchmark batches.

This records synthetic benchmark measurements only. It is not a mesh simulator,
Kalman filter, or autonomous navigation system. NumPy is imported lazily so the
base package remains dependency-light.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .native_wrapper import NativeCore


@dataclass(frozen=True)
class BatchScenario:
    """One deterministic matrix multiplication benchmark case."""

    name: str
    m: int = 128
    k: int = 128
    n: int = 128
    warmup: int = 1
    iterations: int = 3
    seed: int = 7
    verify: bool = True
    require_native: bool = False
    max_memory_bytes: int = 256 * 1024 * 1024


@dataclass(frozen=True)
class ScenarioResult:
    scenario: str
    shape_a: tuple[int, int]
    shape_b: tuple[int, int]
    warmup: int
    iterations: int
    seed: int
    backend: str
    contraction_count: int
    estimated_memory_bytes: int
    min_ms: float
    mean_ms: float
    std_ms: float
    gflops_at_min: float
    max_abs_error: float | None
    timestamp_utc: str


class BatchRunner:
    """Run bounded contraction cases and append machine-readable JSONL records."""

    def __init__(self, output_path: str | Path = ".aether_runs/contraction-benchmarks.jsonl") -> None:
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate(scenario: BatchScenario) -> None:
        if not scenario.name.strip():
            raise ValueError("scenario name must not be empty")
        for field in ("m", "k", "n", "iterations", "max_memory_bytes"):
            value = getattr(scenario, field)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{field} must be a positive integer")
        if isinstance(scenario.warmup, bool) or not isinstance(scenario.warmup, int) or scenario.warmup < 0:
            raise ValueError("warmup must be a non-negative integer")
        if scenario.verify and max(scenario.m, scenario.k, scenario.n) > 2048:
            raise ValueError("verification is limited to dimensions <= 2048")
        # Inputs and output are float64; include a second output buffer when the
        # optional NumPy reference is requested.
        multiplier = 4 if scenario.verify else 3
        estimated = (scenario.m * scenario.k + scenario.k * scenario.n + multiplier * scenario.m * scenario.n) * 8
        if estimated > scenario.max_memory_bytes:
            raise ValueError(
                f"estimated allocation {estimated} bytes exceeds max_memory_bytes "
                f"({scenario.max_memory_bytes})"
            )

    def run_batch(self, scenarios: list[BatchScenario]) -> list[ScenarioResult]:
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("NumPy is required for contraction benchmarks; install numpy") from exc

        results: list[ScenarioResult] = []
        for scenario in scenarios:
            self._validate(scenario)
            core = NativeCore(require_native=scenario.require_native)
            rng = np.random.default_rng(scenario.seed)
            a = np.ascontiguousarray(rng.standard_normal((scenario.m, scenario.k)), dtype=np.float64)
            b = np.ascontiguousarray(rng.standard_normal((scenario.k, scenario.n)), dtype=np.float64)

            for _ in range(scenario.warmup):
                core.contract(a, b)

            durations: list[float] = []
            output = None
            for _ in range(scenario.iterations):
                start = time.perf_counter()
                output = core.contract(a, b)
                durations.append(time.perf_counter() - start)

            max_error: float | None = None
            if scenario.verify:
                reference = a @ b
                max_error = float(np.max(np.abs(output - reference)))
                del reference

            min_seconds = min(durations)
            result = ScenarioResult(
                scenario=scenario.name,
                shape_a=(scenario.m, scenario.k),
                shape_b=(scenario.k, scenario.n),
                warmup=scenario.warmup,
                iterations=scenario.iterations,
                seed=scenario.seed,
                backend="native" if core.use_native else "numpy-fallback",
                contraction_count=core.contraction_count,
                estimated_memory_bytes=(scenario.m * scenario.k + scenario.k * scenario.n + scenario.m * scenario.n) * 8,
                min_ms=min_seconds * 1e3,
                mean_ms=(sum(durations) / len(durations)) * 1e3,
                std_ms=math.sqrt(sum((value - sum(durations) / len(durations)) ** 2 for value in durations) / len(durations)) * 1e3,
                gflops_at_min=(2.0 * scenario.m * scenario.k * scenario.n / min_seconds / 1e9) if min_seconds else 0.0,
                max_abs_error=max_error,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )
            results.append(result)
            with self.output_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(asdict(result), sort_keys=True) + "\n")
            del a, b, output

        return results


__all__ = ["BatchRunner", "BatchScenario", "ScenarioResult"]
