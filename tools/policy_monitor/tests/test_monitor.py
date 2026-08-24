from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.policy_monitor.errors import ValidationError
from tools.policy_monitor.model import load_problem
from tools.policy_monitor.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "policy_monitor" / "off_policy.json"


class PolicyMonitorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)

    def test_exact_doubly_robust_value(self) -> None:
        value = self.report["off_policy"]["doubly_robust_value_bps"]
        self.assertEqual(value["numerator"], 57)
        self.assertEqual(value["denominator"], 8)

    def test_improvement_interval_clears_registered_margin(self) -> None:
        monitor = self.report["off_policy"]
        self.assertEqual(monitor["improvement_bps"]["numerator"], 41)
        self.assertEqual(monitor["improvement_bps"]["denominator"], 8)
        self.assertEqual(monitor["improvement_interval_bps"], [3, 8])
        self.assertTrue(monitor["improvement_passed"])

    def test_effective_sample_size_is_exact_and_sufficient(self) -> None:
        ess = self.report["off_policy"]["effective_sample_size"]
        self.assertEqual(ess["numerator"], 49)
        self.assertEqual(ess["denominator"], 15)
        self.assertTrue(
            self.report["off_policy"]["effective_sample_size_passed"]
        )

    def test_authority_advances_one_level(self) -> None:
        authority = self.report["authority"]
        self.assertEqual(authority["current"], "recommend")
        self.assertEqual(authority["decision"], "microAutonomy")
        self.assertEqual(authority["capital_cap"], 10)

    def test_low_ess_counterfactual_holds_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.json"
            raw = json.loads(MODEL.read_text(encoding="utf-8"))
            raw["records"][0]["behavior_probability_ppm"] = 1
            raw["records"][0]["target_probability_ppm"] = 1_000_000
            path.write_text(json.dumps(raw), encoding="utf-8")
            report = solve(load_problem(path))
            self.assertFalse(
                report["off_policy"]["effective_sample_size_passed"]
            )
            self.assertEqual(report["authority"]["decision"], "recommend")

    def test_model_shift_revokes_even_with_positive_estimate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.json"
            raw = json.loads(MODEL.read_text(encoding="utf-8"))
            raw["model_shift"] = True
            path.write_text(json.dumps(raw), encoding="utf-8")
            report = solve(load_problem(path))
            self.assertEqual(report["authority"]["decision"], "revoked")
            self.assertEqual(report["authority"]["capital_cap"], 0)

    def test_statistical_boundary_is_explicit(self) -> None:
        assurance = self.report["assurance"]
        self.assertTrue(assurance["arithmetic_exact"])
        self.assertTrue(assurance["confidence_sequence_coverage_assumed"])
        self.assertTrue(assurance["optional_stopping_validity_not_proved_in_lean"])

    def test_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["authority"]["capital_cap"] = 100
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
