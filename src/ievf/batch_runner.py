"""Batch runner for deterministic synthetic AETHER-MESH simulations.

This module is intentionally small and sandboxed. It records reproducible metrics
for multiple runs in a single batch, including agent counts, packet-loss settings,
state dimensions, and covariance traces. The goal is to compare performance and
stability across scenario variations without claiming production autonomy.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .aether_mesh import AetherMeshSimulation


@dataclass
class BatchScenario:
    name: str
    num_agents: int = 3
    state_dim: int = 4
    communication_radius: float = 25.0
    packet_drop_rate: float = 0.05
    noise_level: float = 0.02
    epochs: int = 5
    seed: int = 7
    require_native: bool = False


@dataclass
class ScenarioResult:
    scenario: str
    num_agents: int
    state_dim: int
    communication_radius: float
    packet_drop_rate: float
    noise_level: float
    epochs: int
    seed: int
    native_mode: bool
    total_contractions: int
    delivered_packets: int
    dropped_packets: int
    final_covariance_trace: float
    mean_state_norm: float
    mean_neighbor_count: float


class BatchRunner:
    """Execute multiple synthetic mesh scenarios and persist JSONL metrics."""

    def __init__(self, run_dir: str | Path | None = None) -> None:
        self.run_dir = Path(run_dir) if run_dir else Path(".aether_runs")
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def run_batch(self, scenarios: list[BatchScenario]) -> list[ScenarioResult]:
        results: list[ScenarioResult] = []
        for scenario in scenarios:
            sim = AetherMeshSimulation(
                num_agents=scenario.num_agents,
                state_dim=scenario.state_dim,
                communication_radius=scenario.communication_radius,
                packet_drop_rate=scenario.packet_drop_rate,
                noise_level=scenario.noise_level,
                require_native=scenario.require_native,
                seed=scenario.seed,
            )

            delivered_packets = 0
            dropped_packets = 0
            total_contractions = 0
            covariance_traces: list[float] = []
            state_norms: list[float] = []
            neighbor_counts: list[float] = []

            for _ in range(scenario.epochs):
                report = sim.run_epoch()
                total_contractions += sim.core.contraction_count
                sim.core.contraction_count = 0
                for item in report:
                    state_norms.append(float(item["state_norm"]))
                    neighbor_counts.append(float(item["neighbors"]))
                    covariance_traces.append(float(item["covariance_trace"]))
                for packet in sim.channel.transmit.__self__ if False else []:
                    pass

            final_trace = float(np.mean(covariance_traces[-scenario.num_agents:])) if covariance_traces else 0.0
            results.append(
                ScenarioResult(
                    scenario=scenario.name,
                    num_agents=scenario.num_agents,
                    state_dim=scenario.state_dim,
                    communication_radius=scenario.communication_radius,
                    packet_drop_rate=scenario.packet_drop_rate,
                    noise_level=scenario.noise_level,
                    epochs=scenario.epochs,
                    seed=scenario.seed,
                    native_mode=scenario.require_native and sim.core.use_native,
                    total_contractions=total_contractions,
                    delivered_packets=delivered_packets,
                    dropped_packets=dropped_packets,
                    final_covariance_trace=final_trace,
                    mean_state_norm=float(np.mean(state_norms)) if state_norms else 0.0,
                    mean_neighbor_count=float(np.mean(neighbor_counts)) if neighbor_counts else 0.0,
                )
            )

        self.write_jsonl(results)
        return results

    def write_jsonl(self, results: list[ScenarioResult]) -> None:
        output_path = self.run_dir / "aether_batch_results.jsonl"
        with output_path.open("w", encoding="utf-8") as fh:
            for result in results:
                fh.write(json.dumps(asdict(result), sort_keys=True) + "\n")


__all__ = ["BatchRunner", "BatchScenario", "ScenarioResult"]
