from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.certifiable_alpha_interval.errors import ValidationError
from tools.certifiable_alpha_interval.model import load_problem
from tools.certifiable_alpha_interval.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "certifiable_alpha" / "uncertainty.json"


class CertifiableAlphaIntervalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)

    def test_no_evidence_leaves_attack_model_and_cost_uncertainty(self) -> None:
        no_evidence = self.report["no_evidence"]
        self.assertEqual(no_evidence["unresolved_inflation_bps"], 650)
        self.assertEqual(no_evidence["interval_bps"], [-620, 550])
        self.assertEqual(no_evidence["interval_width_bps"], 1170)
        self.assertFalse(no_evidence["meets_target"])

    def test_minimum_evidence_meets_target_width(self) -> None:
        selected = self.report["selected"]
        self.assertEqual(
            selected["channels"], ["pitDataReceipt", "searchLedger"]
        )
        self.assertEqual(selected["cost"], 5)
        self.assertEqual(selected["unresolved_inflation_bps"], 0)
        self.assertEqual(selected["interval_bps"], [30, 550])
        self.assertEqual(selected["interval_width_bps"], 520)
        self.assertTrue(selected["meets_target"])

    def test_attack_identification_does_not_make_alpha_exact(self) -> None:
        selected = self.report["selected"]
        self.assertGreater(selected["interval_width_bps"], 0)
        self.assertEqual(
            self.report["residual_width_after_declared_attack_remediation_bps"],
            520,
        )
        self.assertEqual(self.report["attack_uncertainty_removed_bps"], 650)

    def test_model_envelope_spans_every_declared_model(self) -> None:
        self.assertEqual(self.report["model_envelope_bps"], [150, 600])
        for item in self.report["model_intervals"]:
            self.assertGreaterEqual(item["interval_bps"][0], 150)
            self.assertLessEqual(item["interval_bps"][1], 600)

    def test_every_lower_cost_candidate_fails_the_width_gate(self) -> None:
        for candidate in self.report["lower_cost_failures"]:
            self.assertFalse(candidate["meets_target"])
            self.assertGreater(
                candidate["interval_width_bps"],
                self.report["target_maximum_width_bps"],
            )
            self.assertTrue(candidate["unresolved_distortions"])

    def test_report_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["selected"]["interval_bps"] = [0, 0]
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
