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
    / "gs_quant_generic_data_source.json"
)


class TemporalNoninterferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)
        self.by_operation = {
            item["operation"]: item for item in self.report["pipelines"]
        }

    def test_three_past_only_pipelines_are_safe_and_pure(self) -> None:
        self.assertEqual(self.report["aggregate"]["pipeline_count"], 5)
        self.assertEqual(
            self.report["aggregate"]["causal_and_pure_count"], 3
        )
        for operation in (
            "direct_exact",
            "causal_forward_fill",
            "causal_trailing_mean",
        ):
            item = self.by_operation[operation]
            self.assertTrue(item["temporal_noninterference"])
            self.assertTrue(item["source_immutable"])
            self.assertIsNotNone(item["certificate"])

    def test_append_tail_fill_reproduces_future_extension_leak(self) -> None:
        item = self.by_operation["append_tail_forward_fill"]
        self.assertFalse(item["temporal_noninterference"])
        self.assertFalse(item["source_immutable"])
        self.assertEqual(item["first_divergence"]["time"], 6)
        self.assertEqual(item["first_divergence"]["kind"], "availability_projection")
        self.assertEqual(
            item["base_trace"]["outputs"][-1]["value"], [103, 1]
        )
        self.assertEqual(
            item["extended_trace"]["outputs"][-1]["value"], [999, 1]
        )
        self.assertEqual(
            item["base_trace"]["outputs"][-1]["position"], -1
        )
        self.assertEqual(
            item["extended_trace"]["outputs"][-1]["position"], 1
        )

    def test_two_sided_interpolation_uses_unavailable_right_endpoint(self) -> None:
        item = self.by_operation["two_sided_interpolation"]
        self.assertFalse(item["temporal_noninterference"])
        self.assertTrue(item["availability_projection_differences"])
        full = item["availability_projection_differences"][0]["full_history"]
        prefix = item["availability_projection_differences"][0]["available_prefix"]
        self.assertEqual(full["value"], [310, 3])
        self.assertIsNone(prefix["value"])

    def test_causal_forward_fill_is_future_extension_invariant(self) -> None:
        item = self.by_operation["causal_forward_fill"]
        self.assertEqual(item["future_extension_differences"], [])
        self.assertEqual(item["availability_projection_differences"], [])
        self.assertEqual(
            item["extended_trace"]["outputs"][-1]["value"], [103, 1]
        )

    def test_unsafe_queries_mutate_the_source_model(self) -> None:
        for operation in (
            "append_tail_forward_fill",
            "two_sided_interpolation",
        ):
            item = self.by_operation[operation]
            self.assertTrue(item["base_trace"]["source_mutated"])
            self.assertTrue(item["extended_trace"]["source_mutated"])
            self.assertIsNone(item["certificate"])

    def test_public_issue_regression_is_bound_into_report(self) -> None:
        regression = self.report["gs_quant_generic_data_source_regression"]
        self.assertEqual(regression["public_issue"], "goldmansachs/gs-quant#375")
        self.assertTrue(regression["source_mutated"])
        self.assertEqual(regression["first_divergence"]["time"], 6)

    def test_report_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["aggregate"]["causal_and_pure_count"] = 5
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
