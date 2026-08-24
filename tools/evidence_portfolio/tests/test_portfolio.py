from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.evidence_portfolio.errors import ValidationError
from tools.evidence_portfolio.model import load_problem
from tools.evidence_portfolio.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "evidence_portfolio" / "hidden_common_risk.json"


class EvidencePortfolioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)

    def test_raw_objective_selects_the_shared_vendor_pair(self) -> None:
        raw = self.report["raw_optimum"]
        self.assertEqual(
            raw["strategies"], ["vendorMomentum", "vendorValue"]
        )
        self.assertEqual(raw["dependency_concentration"], 1)
        self.assertEqual(
            raw["dependency_pairs"][0]["shared_domains"], ["vendor-a"]
        )

    def test_evidence_adjusted_objective_selects_independent_pair(self) -> None:
        adjusted = self.report["evidence_adjusted_optimum"]
        self.assertEqual(
            adjusted["strategies"],
            ["independentQuality", "independentTrend"],
        )
        self.assertEqual(adjusted["dependency_concentration"], 0)
        self.assertEqual(adjusted["evidence_debt"], 2)
        self.assertEqual(adjusted["robustness"], 8)

    def test_selection_change_improves_the_declared_adjusted_objective(self) -> None:
        self.assertTrue(self.report["selection_changed"])
        self.assertEqual(self.report["raw_optimum_adjusted_score"], 320)
        self.assertEqual(
            self.report["evidence_adjusted_optimum"]["evidence_adjusted"]["score"],
            600,
        )
        self.assertEqual(self.report["adjusted_optimum_score_gain"], 280)

    def test_exact_candidate_space_contains_every_pair(self) -> None:
        self.assertEqual(self.report["candidate_count"], 6)
        self.assertEqual(len(self.report["candidates"]), 6)
        selected_score = self.report["evidence_adjusted_optimum"][
            "evidence_adjusted"
        ]["score"]
        self.assertTrue(all(
            candidate["evidence_adjusted"]["score"] <= selected_score
            for candidate in self.report["candidates"]
        ))

    def test_score_breakdowns_reconcile(self) -> None:
        for candidate in self.report["candidates"]:
            raw = candidate["raw"]
            self.assertEqual(
                raw["score"], raw["alpha_component"] - raw["risk_penalty"]
            )
            adjusted = candidate["evidence_adjusted"]
            self.assertEqual(
                adjusted["score"],
                adjusted["alpha_component"]
                - adjusted["risk_penalty"]
                - adjusted["debt_penalty"]
                + adjusted["robustness_reward"]
                - adjusted["dependency_penalty"],
            )

    def test_report_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["adjusted_optimum_score_gain"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
