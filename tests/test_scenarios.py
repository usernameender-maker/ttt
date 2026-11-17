"""Deterministic validation tests for bounded benchmark scenarios."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from ievf.native_wrapper import NativeCore

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_PATH = ROOT / "research-data" / "scenarios.json"


class TestScenarioContracts(unittest.TestCase):
    def test_scenario_catalog_is_valid(self) -> None:
        payload = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
        scenarios = payload["scenarios"]
        self.assertTrue(scenarios)

        for scenario in scenarios:
            self.assertIn("name", scenario)
            self.assertIn("rows", scenario)
            self.assertIn("cols_a", scenario)
            self.assertIn("cols_b", scenario)
            self.assertIn("seed", scenario)
            self.assertIn("tolerance", scenario)

            self.assertGreater(scenario["rows"], 0)
            self.assertGreater(scenario["cols_a"], 0)
            self.assertGreater(scenario["cols_b"], 0)
            self.assertGreaterEqual(scenario["tolerance"], 0.0)

            rng = np.random.default_rng(scenario["seed"])
            a = np.ascontiguousarray(
                rng.standard_normal((scenario["rows"], scenario["cols_a"])),
                dtype=np.float64,
            )
            b = np.ascontiguousarray(
                rng.standard_normal((scenario["cols_a"], scenario["cols_b"])),
                dtype=np.float64,
            )

            output = NativeCore(require_native=False).contract(a, b)
            reference = a @ b
            self.assertTrue(np.all(np.isfinite(output)))
            self.assertTrue(np.all(np.isfinite(reference)))
            self.assertLessEqual(
                float(np.max(np.abs(output - reference))),
                float(scenario["tolerance"]),
            )


if __name__ == "__main__":
    unittest.main()
