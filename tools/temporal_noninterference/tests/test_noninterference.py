from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.temporal_noninterference.errors import ValidationError
from tools.temporal_noninterference.model import load_problem
from tools.temporal_noninterference.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = (
    ROOT
    / "examples"
    / "temporal_noninterference"
    / "future_extension.json"
)


class TemporalNoninterferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)
        self.by_id = {
            row["id"]: row for row in self.report["transforms"]
        }

    def test_histories_are_equivalent_through_cutoff(self) -> None:
        self.assertTrue(
            self.report["histories_equivalent_through_cutoff"]
        )
        self.assertEqual(
            self.report["base_prefix"], self.report["extended_prefix"]
        )

    def test_direct_and_causal_forward_fill_are_safe(self) -> None:
        self.assertTrue(self.by_id["directObservation"]["noninterfering"])
        causal = self.by_id["causalForwardFill"]
        self.assertTrue(causal["noninterfering"])
        self.assertEqual(
            [item["output"] for item in causal["base_outputs"]],
            [100, 110, 120],
        )
        self.assertEqual(causal["minimal_future_extension_ids"], [])

    def test_terminal_fill_has_an_early_future_extension_witness(self) -> None:
        row = self.by_id["terminalValueFillBug"]
        self.assertFalse(row["noninterfering"])
        self.assertEqual(
            row["first_divergence"],
            {"query_time": 2, "base_output": 120, "extended_output": 999},
        )
        self.assertEqual(
            row["minimal_future_extension_ids"], ["futureExtreme"]
        )
        self.assertIn("filterByAvailableAt", row["repair_obligations"])

    def test_two_sided_interpolation_uses_a_future_right_endpoint(self) -> None:
        row = self.by_id["twoSidedInterpolation"]
        self.assertFalse(row["noninterfering"])
        self.assertEqual(row["first_divergence"]["query_time"], 6)
        self.assertIsNone(row["first_divergence"]["base_output"])
        self.assertEqual(row["first_divergence"]["extended_output"], 295)

    def test_whole_sample_statistics_rewrite_past_outputs(self) -> None:
        row = self.by_id["wholeSampleCentering"]
        self.assertFalse(row["noninterfering"])
        self.assertEqual(row["first_divergence"]["query_time"], 2)
        self.assertEqual(row["first_divergence"]["base_output"], -10)
        self.assertEqual(row["first_divergence"]["extended_output"], -232)
        self.assertIn(
            "fitStatisticsThroughDecisionCutoff",
            row["repair_obligations"],
        )

    def test_all_declared_expectations_match(self) -> None:
        self.assertEqual(self.report["aggregate"]["transform_count"], 5)
        self.assertEqual(self.report["aggregate"]["noninterfering_count"], 2)
        self.assertEqual(self.report["aggregate"]["violation_count"], 3)
        self.assertTrue(self.report["aggregate"]["all_expectations_met"])

    def test_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["aggregate"]["violation_count"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
