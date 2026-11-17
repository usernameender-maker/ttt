"""Validate small research scenarios on the native matrix backend.

Larger manifest scenarios remain benchmark workloads rather than unit tests so
routine test discovery cannot accidentally become a long performance run.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest("research scenario tests require optional NumPy") from exc

from ievf.batch_runner import BatchRunner, BatchScenario
from ievf.native_wrapper import NativeCore


class TestResearchScenarios(unittest.TestCase):
    """Check manifest validity and native correctness for bounded small cases."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root_dir = Path(__file__).resolve().parent.parent
        path = cls.root_dir / "research-data" / "scenarios.json"
        with path.open(encoding="utf-8") as stream:
            manifest = json.load(stream)
        if manifest.get("schema_version") != 1:
            raise AssertionError("unsupported research scenario schema_version")
        rows = manifest.get("scenarios")
        if not isinstance(rows, list) or not rows:
            raise AssertionError("research scenario manifest must contain scenarios")
        cls.scenarios = [BatchScenario(**row) for row in rows]

    def test_scenarios_are_valid_and_memory_bounded(self) -> None:
        names = set()
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario.name):
                self.assertNotIn(scenario.name, names, "scenario names must be unique")
                names.add(scenario.name)
                BatchRunner._validate(scenario)
                self.assertTrue(scenario.verify, "research scenarios must enable verification")
                self.assertTrue(scenario.require_native, "research scenarios must require native backend")

    def test_small_scenarios_match_numpy_on_native_backend(self) -> None:
        # Keep unit-test runtime predictable; 512/1024 cases are run by the
        # explicit benchmark runner, not by normal test discovery.
        scenarios = [s for s in self.scenarios if max(s.m, s.k, s.n) <= 256]
        self.assertTrue(scenarios, "manifest must include at least one small scenario")

        try:
            core = NativeCore(require_native=True)
        except RuntimeError as exc:
            raise unittest.SkipTest(f"native extension is not available: {exc}") from exc
        self.assertTrue(core.use_native, "strict native mode must not silently use fallback")

        for scenario in scenarios:
            with self.subTest(scenario=scenario.name):
                rng = np.random.default_rng(scenario.seed)
                a = np.ascontiguousarray(rng.standard_normal((scenario.m, scenario.k)), dtype=np.float64)
                b = np.ascontiguousarray(rng.standard_normal((scenario.k, scenario.n)), dtype=np.float64)
                actual = core.contract(a, b)
                reference = a @ b

                self.assertEqual(actual.shape, reference.shape)
                self.assertTrue(np.all(np.isfinite(actual)), "native result must be finite")
                np.testing.assert_allclose(actual, reference, rtol=1e-10, atol=1e-12)
                self.assertIsNotNone(scenario.max_memory_bytes)


if __name__ == "__main__":
    unittest.main()
