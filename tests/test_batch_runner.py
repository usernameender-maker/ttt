import json
import tempfile
import unittest
from pathlib import Path

try:
    import numpy as np  # noqa: F401
except ImportError as exc:
    raise unittest.SkipTest("batch benchmark tests require optional NumPy") from exc

from ievf.batch_runner import BatchRunner, BatchScenario


class BatchRunnerTests(unittest.TestCase):
    def test_runs_and_records_reproducible_case(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs.jsonl"
            runner = BatchRunner(path)
            result = runner.run_batch([
                BatchScenario("small", m=3, k=4, n=2, warmup=0, iterations=1, seed=9)
            ])[0]
            self.assertEqual(result.shape_a, (3, 4))
            self.assertEqual(result.shape_b, (4, 2))
            self.assertIsNotNone(result.max_abs_error)
            self.assertLess(result.max_abs_error, 1e-12)
            self.assertEqual(result.contraction_count, 1)
            row = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(row["scenario"], "small")
            self.assertIn(row["backend"], {"native", "numpy-fallback"})

    def test_memory_limit_rejects_case_before_allocation(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = BatchRunner(Path(directory) / "runs.jsonl")
            scenario = BatchScenario("too-large", m=100, k=100, n=100, max_memory_bytes=100)
            with self.assertRaisesRegex(ValueError, "exceeds max_memory_bytes"):
                runner.run_batch([scenario])

    def test_verification_dimension_limit(self):
        scenario = BatchScenario("oversized-reference", m=2049, k=1, n=1, verify=True)
        with self.assertRaisesRegex(ValueError, "verification is limited"):
            BatchRunner._validate(scenario)


if __name__ == "__main__":
    unittest.main()
