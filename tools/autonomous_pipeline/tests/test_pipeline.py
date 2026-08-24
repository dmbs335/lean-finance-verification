from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.autonomous_pipeline.errors import ValidationError
from tools.autonomous_pipeline.model import load_problem
from tools.autonomous_pipeline.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "autonomous_pipeline" / "pipeline.json"


class AutonomousPipelineCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)

    def test_local_certificates_are_valid_but_do_not_compose(self) -> None:
        claims = self.report["controlled_claims"]
        self.assertTrue(claims["all_local_certificates_valid"])
        self.assertTrue(claims["local_summary_cannot_verify_global_pipeline"])
        self.assertFalse(self.report["local_summary_only"]["verifies"])

    def test_exact_minimum_uses_five_narrow_receipts(self) -> None:
        selected = self.report["synthesis"]["selected"]
        self.assertEqual(
            selected["channels"],
            [
                "datasetStateBindingReceipt",
                "decisionInputBindingReceipt",
                "decisionAuthorizationBindingReceipt",
                "authorizationExecutionBindingReceipt",
                "executionReconciliationBindingReceipt",
            ],
        )
        self.assertEqual(selected["cost"], 6)
        self.assertTrue(selected["verifies"])
        self.assertEqual(selected, self.report["all_bridge_receipts"])

    def test_global_bundle_is_sufficient_but_more_expensive(self) -> None:
        global_bundle = self.report["global_bundle_only"]
        self.assertTrue(global_bundle["verifies"])
        self.assertEqual(global_bundle["cost"], 9)

    def test_every_lower_cost_candidate_has_a_counterexample(self) -> None:
        failures = self.report["synthesis"]["lower_cost_failures"]
        self.assertTrue(failures)
        for candidate in failures:
            self.assertFalse(candidate["verifies"])
            self.assertIn("uncovered", candidate)

    def test_worlds_break_each_binding_independently(self) -> None:
        broken = {
            world["id"] for world in self.report["worlds"]
            if world["id"].startswith("broken:")
        }
        self.assertEqual(len(broken), 6)

    def test_missing_digest_binding_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.json"
            raw = json.loads(MODEL.read_text(encoding="utf-8"))
            raw["artifacts"]["decision"]["input_sha256"] = ["b" * 64]
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "binding"):
                load_problem(path)

    def test_tampered_report_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["synthesis"]["selected"]["cost"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
