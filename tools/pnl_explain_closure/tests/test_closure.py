from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.pnl_explain_closure.analyzer import analyze, verify
from tools.pnl_explain_closure.errors import ValidationError
from tools.pnl_explain_closure.model import load_problem

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "pnl_explain_closure" / "controlled.json"


class PnlExplainClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = analyze(self.problem)
        self.by_id = {case["id"]: case for case in self.report["cases"]}

    def test_upstream_reference_is_static_theory_mapping(self) -> None:
        upstream = self.report["upstream_reference"]
        self.assertEqual(upstream["repository"], "goldmansachs/gs-quant")
        self.assertEqual(upstream["release"], "2.1.6")
        self.assertEqual(upstream["symbol"], "BackTest.pnl_explain")
        self.assertEqual(
            upstream["coverage_status"], "STATIC_REVIEW_THEORY_MAPPED"
        )

    def test_closed_case_has_exact_quadratic_terms_and_small_residual(self) -> None:
        case = self.by_id["closed-small-residual"]
        self.assertEqual(case["status"], "CLOSED")
        self.assertTrue(case["local_and_binding_valid"])
        self.assertEqual(case["market_explained_pnl"], 44)
        self.assertEqual(case["non_market_total_pnl"], 16)
        self.assertEqual(case["reconstructed_pnl"], 60)
        self.assertEqual(case["realized_pnl"], 61)
        self.assertEqual(case["residual"], 1)
        self.assertTrue(case["residual_within_tolerance"])

    def test_partial_case_is_arithmetically_bound_but_materially_unexplained(self) -> None:
        case = self.by_id["partial-material-residual"]
        self.assertEqual(case["status"], "PARTIAL")
        self.assertTrue(case["local_and_binding_valid"])
        self.assertEqual(case["residual"], 10)
        self.assertFalse(case["residual_within_tolerance"])
        self.assertTrue(any("material residual" in reason for reason in case["reasons"]))

    def test_local_formula_validity_does_not_imply_global_binding(self) -> None:
        case = self.by_id["open-substituted-portfolio"]
        self.assertEqual(case["status"], "OPEN")
        self.assertTrue(case["local_formulas_valid"])
        self.assertFalse(case["factor_bindings_valid"])
        witness = case["constructive_binding_counterexample"]
        self.assertIsNotNone(witness)
        self.assertEqual(witness["mismatched_factor_ids"], ["delta-gamma"])

    def test_formula_mismatch_keeps_case_open(self) -> None:
        case = self.by_id["open-formula-mismatch"]
        self.assertEqual(case["status"], "OPEN")
        self.assertFalse(case["local_formulas_valid"])
        factor = next(f for f in case["factors"] if f["id"] == "delta-gamma")
        self.assertEqual(factor["expected_first_order_pnl"], 30)
        self.assertEqual(factor["claimed_first_order_pnl"], 31)

    def test_future_input_keeps_case_open(self) -> None:
        case = self.by_id["open-future-attribution"]
        self.assertEqual(case["status"], "OPEN")
        self.assertFalse(case["factors_temporally_valid"])
        self.assertEqual(
            self.report["aggregate"]["temporal_failure_count"], 1
        )

    def test_transaction_cost_is_subtracted(self) -> None:
        case = self.by_id["closed-small-residual"]
        components = case["non_market"]
        expected = (
            components["carry"]
            + components["trades"]
            + components["cashflows"]
            - components["transaction_cost"]
            + components["model_revision"]
        )
        self.assertEqual(case["non_market_total_pnl"], expected)

    def test_expected_status_distribution(self) -> None:
        self.assertEqual(
            self.report["aggregate"],
            {
                "closed_count": 1,
                "partial_count": 1,
                "open_count": 3,
                "formula_failure_count": 1,
                "binding_failure_count": 1,
                "temporal_failure_count": 1,
                "material_residual_count": 1,
            },
        )

    def test_report_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["cases"][0]["residual"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_analyzer_is_deterministic(self) -> None:
        self.assertEqual(self.report, analyze(self.problem))


if __name__ == "__main__":
    unittest.main()
