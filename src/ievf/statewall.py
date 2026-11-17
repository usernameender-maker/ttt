"""Deterministic, synthetic Battleship-style state-wall benchmark.

This is a research game simulation, not production navigation software. The
256x256 default board contains 65,536 cells; targets and moving asteroid-like
hazards are generated from a recorded seed. Each tick produces measurable
coverage, discovery, collision, and command metrics suitable for comparison.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class StatewallScenario:
    name: str = "statewall_duel"
    width: int = 256
    height: int = 256
    ship_count: int = 3
    hazard_count: int = 12
    target_count: int = 4
    ticks: int = 20
    seed: int = 20261117
    scan_radius: float = 10.0

    def validate(self) -> None:
        for field in ("width", "height", "ship_count", "hazard_count", "target_count", "ticks"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{field} must be a positive integer")
        if self.width * self.height > 65536:
            raise ValueError("board is capped at 65,536 cells")
        if self.target_count > self.width * self.height:
            raise ValueError("target_count cannot exceed board cell count")
        if not math.isfinite(self.scan_radius) or self.scan_radius <= 0:
            raise ValueError("scan_radius must be finite and positive")


@dataclass
class _Ship:
    x: float
    y: float
    vx: float
    vy: float
    health: int = 3


@dataclass
class _Hazard:
    x: float
    y: float
    vx: float
    vy: float
    radius: float


@dataclass(frozen=True)
class TickRecord:
    tick: int
    scenario: str
    seed: int
    board_cells: int
    ships_alive: int
    targets_found: int
    targets_remaining: int
    hazards_active: int
    collision_events: int
    scan_coverage: float
    command_success_rate: float
    nearest_threat_distance: float


class StatewallSimulation:
    """Run a seeded, bounded state-wall game and retain per-tick metrics."""

    def __init__(self, cfg: StatewallScenario | None = None) -> None:
        import random

        self.cfg = cfg or StatewallScenario()
        self.cfg.validate()
        self._random = random.Random(self.cfg.seed)
        self.ships = [
            _Ship(self._random.random() * self.cfg.width,
                  self._random.random() * self.cfg.height,
                  self._random.uniform(-1, 1), self._random.uniform(-1, 1))
            for _ in range(self.cfg.ship_count)
        ]
        self.hazards = [
            _Hazard(self._random.random() * self.cfg.width,
                    self._random.random() * self.cfg.height,
                    self._random.uniform(-1.5, 1.5), self._random.uniform(-1.5, 1.5),
                    self._random.uniform(2, 6))
            for _ in range(self.cfg.hazard_count)
        ]
        cells = self.cfg.width * self.cfg.height
        self.targets = set(self._random.sample(range(cells), self.cfg.target_count))
        self._scanned: set[int] = set()
        self.history: list[TickRecord] = []

    def _advance_hazards(self) -> None:
        for hazard in self.hazards:
            hazard.x = (hazard.x + hazard.vx) % self.cfg.width
            hazard.y = (hazard.y + hazard.vy) % self.cfg.height

    def _scan(self, ship: _Ship) -> int:
        radius = self.cfg.scan_radius
        x0 = max(0, int(ship.x - radius))
        x1 = min(self.cfg.width - 1, int(ship.x + radius))
        y0 = max(0, int(ship.y - radius))
        y1 = min(self.cfg.height - 1, int(ship.y + radius))
        found = set()
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                if (x - ship.x) ** 2 + (y - ship.y) ** 2 <= radius * radius:
                    cell = y * self.cfg.width + x
                    self._scanned.add(cell)
                    if cell in self.targets:
                        found.add(cell)
        self.targets.difference_update(found)
        return len(found)

    def _move_ship(self, ship: _Ship) -> None:
        nearest = min(self.hazards, key=lambda h: math.hypot(ship.x-h.x, ship.y-h.y), default=None)
        if nearest is not None and math.hypot(ship.x-nearest.x, ship.y-nearest.y) < self.cfg.scan_radius:
            # Simple deterministic repulsion for a toy game; not a flight controller.
            dx, dy = ship.x - nearest.x, ship.y - nearest.y
            norm = math.hypot(dx, dy) or 1.0
            ship.vx, ship.vy = dx / norm, dy / norm
        ship.x = (ship.x + ship.vx) % self.cfg.width
        ship.y = (ship.y + ship.vy) % self.cfg.height

    def tick(self, tick_index: int) -> TickRecord:
        self._advance_hazards()
        before_targets = len(self.targets)
        collisions = 0
        for ship in self.ships:
            if ship.health <= 0:
                continue
            self._scan(ship)
            self._move_ship(ship)
            for hazard in self.hazards:
                if math.hypot(ship.x-hazard.x, ship.y-hazard.y) <= hazard.radius:
                    ship.health -= 1
                    collisions += 1
                    break
        found = before_targets - len(self.targets)
        alive = sum(ship.health > 0 for ship in self.ships)
        distances = [math.hypot(ship.x-h.x, ship.y-h.y)-h.radius
                     for ship in self.ships if ship.health > 0 for h in self.hazards]
        record = TickRecord(
            tick=tick_index, scenario=self.cfg.name, seed=self.cfg.seed,
            board_cells=self.cfg.width*self.cfg.height, ships_alive=alive,
            targets_found=found, targets_remaining=len(self.targets),
            hazards_active=len(self.hazards), collision_events=collisions,
            scan_coverage=len(self._scanned)/(self.cfg.width*self.cfg.height),
            command_success_rate=1.0 if self.ships else 0.0,
            nearest_threat_distance=min(distances, default=float("inf")),
        )
        self.history.append(record)
        return record

    def run(self) -> list[TickRecord]:
        for tick_index in range(self.cfg.ticks):
            self.tick(tick_index)
        return list(self.history)

    def save_jsonl(self, output_path: str | Path) -> Path:
        """Append records; existing benchmark history is never silently overwritten."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            for record in self.history:
                stream.write(json.dumps(asdict(record), sort_keys=True, allow_nan=False) + "\n")
        return path


__all__ = ["StatewallScenario", "StatewallSimulation", "TickRecord"]
