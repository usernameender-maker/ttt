"""Tests for benchmark JSONL persistence and memory guards."""
import json
import tempfile
import unittest
from pathlib import Path

try:
    import numpy  # noqa: F401
except ImportError as exc:
    raise unittest.SkipTest("benchmark tests require optional NumPy") from exc

from ievf.batch_runner import BatchRunner, BatchScenario


class BatchRunnerTests(unittest.TestCase):
    def test_run_logs_correctness_and_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bench.jsonl"
            results = BatchRunner(path).run_batch([BatchScenario("tiny", 3, 4, 2, 0, 1, 9)])
            self.assertLess(results[0].max_abs_error, 1e-12)
            self.assertEqual(results[0].contraction_count, 1)
            row = json.loads(path.read_text().splitlines()[0])
            self.assertEqual(row["scenario"], "tiny")

    def test_memory_limit_rejects_before_allocation(self):
        case = BatchScenario("large", m=100, k=100, n=100, max_memory_bytes=100)
        with self.assertRaisesRegex(ValueError, "exceeds max_memory_bytes"):
            BatchRunner._validate(case)

    def test_verification_dimension_limit(self):
        with self.assertRaisesRegex(ValueError, "verification is limited"):
            BatchRunner._validate(BatchScenario("large-ref", m=2049, k=1, n=1))


if __name__ == "__main__":
    unittest.main()
