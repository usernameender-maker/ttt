"""Tests for the deterministic synthetic state-wall benchmark."""
import json
import tempfile
import unittest
from pathlib import Path

from ievf.statewall import StatewallScenario, StatewallSimulation


class StatewallTests(unittest.TestCase):
    def test_tick_produces_valid_record(self):
        sim = StatewallSimulation(StatewallScenario(name="mini", width=32, height=32, ship_count=2, hazard_count=3, target_count=2, ticks=2, seed=11))
        record = sim.tick(0)
        self.assertEqual(record.tick, 0)
        self.assertEqual(record.board_cells, 1024)
        self.assertGreaterEqual(record.ships_alive, 0)
        self.assertGreaterEqual(record.command_success_rate, 0.0)
        self.assertLessEqual(record.scan_coverage, 1.0)

    def test_same_seed_reproduces_records(self):
        cfg = StatewallScenario(name="repeat", width=32, height=32, ship_count=2, hazard_count=2, target_count=2, ticks=3, seed=17)
        a, b = StatewallSimulation(cfg).run(), StatewallSimulation(cfg).run()
        self.assertEqual(a, b)

    def test_jsonl_appends_records(self):
        cfg = StatewallScenario(name="jsonl", width=32, height=32, ship_count=2, hazard_count=2, target_count=1, ticks=2, seed=29)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "statewall.jsonl"
            sim = StatewallSimulation(cfg)
            sim.run()
            sim.save_jsonl(path)
            sim.save_jsonl(path)
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(rows), 4)
            self.assertEqual(rows[0]["scenario"], "jsonl")

    def test_board_limit(self):
        with self.assertRaisesRegex(ValueError, "65,536"):
            StatewallSimulation(StatewallScenario(width=257, height=256))


if __name__ == "__main__":
    unittest.main()
