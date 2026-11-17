"""Memory-bounded synthetic matrix-contraction benchmark batches."""
from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .native_wrapper import NativeCore


@dataclass(frozen=True)
class BatchScenario:
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
    """Run bounded matrix cases and append each result to a JSONL ledger."""

    def __init__(self, output_path: str | Path = ".aether_runs/contraction-benchmarks.jsonl") -> None:
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate(s: BatchScenario) -> int:
        if not s.name.strip():
            raise ValueError("scenario name must not be empty")
        for key in ("m", "k", "n", "iterations", "max_memory_bytes"):
            value = getattr(s, key)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{key} must be a positive integer")
        if isinstance(s.warmup, bool) or not isinstance(s.warmup, int) or s.warmup < 0:
            raise ValueError("warmup must be a non-negative integer")
        if s.verify and max(s.m, s.k, s.n) > 2048:
            raise ValueError("verification is limited to dimensions <= 2048")
        # Inputs, output and optional independent reference, float64.
        multiplier = 4 if s.verify else 3
        estimate = (s.m*s.k + s.k*s.n + multiplier*s.m*s.n) * 8
        if estimate > s.max_memory_bytes:
            raise ValueError(f"estimated allocation {estimate} bytes exceeds max_memory_bytes ({s.max_memory_bytes})")
        return estimate

    def run_batch(self, scenarios: list[BatchScenario]) -> list[ScenarioResult]:
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("NumPy is required; install the optional native dependencies") from exc
        results = []
        for scenario in scenarios:
            estimate = self._validate(scenario)
            core = NativeCore(require_native=scenario.require_native)
            rng = np.random.default_rng(scenario.seed)
            a = np.ascontiguousarray(rng.standard_normal((scenario.m, scenario.k)), dtype=np.float64)
            b = np.ascontiguousarray(rng.standard_normal((scenario.k, scenario.n)), dtype=np.float64)
            for _ in range(scenario.warmup):
                core.contract(a, b)
            samples = []
            output = None
            for _ in range(scenario.iterations):
                start = time.perf_counter()
                output = core.contract(a, b)
                samples.append(time.perf_counter() - start)
            error = None
            if scenario.verify:
                reference = a @ b
                error = float(np.max(np.abs(output-reference))) if output.size else 0.0
                del reference
            mean = sum(samples)/len(samples)
            best = min(samples)
            result = ScenarioResult(
                scenario=scenario.name, shape_a=(scenario.m, scenario.k), shape_b=(scenario.k, scenario.n),
                seed=scenario.seed, backend="native" if core.use_native else "numpy-fallback",
                contraction_count=core.contraction_count, estimated_memory_bytes=estimate,
                min_ms=best*1e3, mean_ms=mean*1e3,
                std_ms=math.sqrt(sum((x-mean)**2 for x in samples)/len(samples))*1e3,
                gflops_at_min=(2*scenario.m*scenario.k*scenario.n/best/1e9) if best else 0.0,
                max_abs_error=error, timestamp_utc=datetime.now(timezone.utc).isoformat())
            results.append(result)
            with self.output_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(asdict(result), sort_keys=True, allow_nan=False)+"\n")
            del a, b, output
        return results


__all__ = ["BatchRunner", "BatchScenario", "ScenarioResult"]
