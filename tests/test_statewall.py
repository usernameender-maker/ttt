import json
import tempfile
import unittest
from pathlib import Path

from ievf.statewall import StatewallScenario, StatewallSimulation


class StatewallTests(unittest.TestCase):
    def test_tick_produces_valid_state_record(self):
        sim = StatewallSimulation(StatewallScenario(name="mini", ship_count=2, hazard_count=3, target_count=2, ticks=2, seed=11))
        record = sim.tick(0)
        self.assertEqual(record.tick, 0)
        self.assertGreaterEqual(record.ships_alive, 1)
        self.assertGreaterEqual(record.hazards_active, 1)
        self.assertGreaterEqual(record.command_success_rate, 0.0)
        self.assertLessEqual(record.command_success_rate, 1.0)

    def test_run_records_multiple_ticks(self):
        sim = StatewallSimulation(StatewallScenario(name="mini-run", ship_count=2, hazard_count=2, target_count=1, ticks=3, seed=17))
        history = sim.run()
        self.assertEqual(len(history), 3)
        self.assertTrue(all(record.scenario == "mini-run" for record in history))

    def test_save_jsonl_writes_records(self):
        sim = StatewallSimulation(StatewallScenario(name="jsonl", ship_count=2, hazard_count=2, target_count=1, ticks=2, seed=29))
        sim.run()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "statewall.jsonl"
            written = sim.save_jsonl(path)
            self.assertTrue(written.exists())
            rows = [json.loads(line) for line in written.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["scenario"], "jsonl")


if __name__ == "__main__":
    unittest.main()
