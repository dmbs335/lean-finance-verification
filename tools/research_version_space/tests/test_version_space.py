from __future__ import annotations

import copy
import unittest
from fractions import Fraction
from pathlib import Path

from tools.research_version_space.errors import ValidationError
from tools.research_version_space.model import load_problem
from tools.research_version_space.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = (
    ROOT
    / "examples"
    / "research_version_space"
    / "five_dimensions.json"
)


class ResearchVersionSpaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)

    def test_cartesian_world_and_channel_spaces_are_exhaustive(self) -> None:
        self.assertEqual(self.report["dimension_count"], 5)
        self.assertEqual(self.report["world_count"], 32)
        self.assertEqual(self.report["channel_count"], 6)
        self.assertEqual(self.report["candidate_count"], 64)

    def test_no_evidence_leaves_a_wide_interacting_range(self) -> None:
        no_evidence = self.report["no_evidence"]
        self.assertEqual(no_evidence["range"], [20, 150])
        self.assertEqual(no_evidence["width"], 130)
        self.assertEqual(no_evidence["admissible_world_count"], 32)
        self.assertFalse(no_evidence["meets_target"])

    def test_minimum_target_evidence_is_data_plus_search(self) -> None:
        selected = self.report["synthesis"]["selected"]
        self.assertEqual(
            selected["channels"], ["pitDataReceipt", "searchLedger"]
        )
        self.assertEqual(selected["cost"], 4)
        self.assertEqual(selected["restricted_dimensions"], ["data", "search"])
        self.assertEqual(selected["range"], [20, 55])
        self.assertEqual(selected["width"], 35)
        self.assertEqual(selected["admissible_world_count"], 8)
        self.assertTrue(selected["meets_target"])

    def test_every_lower_cost_candidate_has_a_range_counterexample(self) -> None:
        failures = self.report["synthesis"]["lower_cost_failures"]
        self.assertTrue(failures)
        for candidate in failures:
            self.assertFalse(candidate["meets_target"])
            witness = candidate["width_counterexample"]
            self.assertGreater(
                witness["upper_world"]["metric"]
                - witness["lower_world"]["metric"],
                self.report["target_maximum_width"],
            )
            self.assertTrue(witness["differing_dimensions"])

    def test_full_identification_prefers_unified_bundle(self) -> None:
        point = self.report["minimum_point_identification"]
        self.assertEqual(point["channels"], ["unifiedResearchBundle"])
        self.assertEqual(point["cost"], 8)
        self.assertEqual(point["range"], [20, 20])
        self.assertEqual(point["admissible_world_count"], 1)

    def test_exact_shapley_attribution_includes_interactions(self) -> None:
        values = {
            item["dimension"]: Fraction(
                item["contribution"]["numerator"],
                item["contribution"]["denominator"],
            )
            for item in self.report[
                "shapley_revision_attribution"
            ]["contributions"]
        }
        self.assertEqual(values["data"], Fraction(105, 2))
        self.assertEqual(values["model"], Fraction(10, 1))
        self.assertEqual(values["search"], Fraction(85, 2))
        self.assertEqual(values["execution"], Fraction(35, 2))
        self.assertEqual(values["universe"], Fraction(15, 2))
        self.assertEqual(sum(values.values(), Fraction(0)), Fraction(130))

    def test_flip_effects_reveal_context_sensitive_interactions(self) -> None:
        by_dimension = {
            item["dimension"]: item
            for item in self.report["dimension_flip_effects"]
        }
        self.assertEqual(
            (by_dimension["data"]["minimum_effect"],
             by_dimension["data"]["maximum_effect"]),
            (40, 65),
        )
        self.assertEqual(
            (by_dimension["search"]["minimum_effect"],
             by_dimension["search"]["maximum_effect"]),
            (30, 55),
        )
        self.assertFalse(by_dimension["model"]["context_sensitive"])
        self.assertTrue(by_dimension["execution"]["context_sensitive"])
        self.assertTrue(by_dimension["universe"]["context_sensitive"])

    def test_every_evidence_refinement_nests_the_exact_range(self) -> None:
        refinement = self.report["refinement_checks"]
        self.assertTrue(refinement["all_ranges_nested"])
        self.assertEqual(refinement["violations"], [])
        self.assertGreater(refinement["checked_pair_count"], 64)

    def test_report_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["synthesis"]["selected"]["width"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
