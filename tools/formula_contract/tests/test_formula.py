from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.formula_contract.errors import ValidationError
from tools.formula_contract.model import load_problem
from tools.formula_contract.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "formula_contract" / "hedge_scale.json"


class FormulaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)
        self.by_id = {
            item["application"]: item
            for item in self.report["applications"]
        }

    def test_only_complete_application_receives_certificate(self) -> None:
        self.assertEqual(self.report["application_count"], 7)
        self.assertEqual(
            self.report["aggregate"]["valid_application_count"], 1
        )
        valid = self.by_id["validHedgeScale"]
        self.assertTrue(valid["passes"])
        self.assertEqual(valid["computed_result"], [3, 4])
        self.assertEqual(valid["claimed_result"], [3, 4])
        self.assertIsNotNone(valid["certificate"])

    def test_future_input_is_rejected_despite_correct_number(self) -> None:
        item = self.by_id["futureRiskInput"]
        self.assertTrue(item["checks"]["definition_matched"])
        self.assertTrue(item["checks"]["result_bound"])
        self.assertFalse(item["checks"]["inputs_available"])
        self.assertTrue(item["formula_correct_but_application_invalid"])
        self.assertIsNone(item["certificate"])

    def test_unit_mismatch_is_rejected(self) -> None:
        item = self.by_id["currencyUnitMismatch"]
        self.assertFalse(item["checks"]["units_valid"])
        self.assertIn("units_valid", item["failed_obligations"])

    def test_model_version_mismatch_is_rejected(self) -> None:
        item = self.by_id["modelVersionMismatch"]
        self.assertFalse(item["checks"]["model_aligned"])
        self.assertTrue(item["checks"]["result_bound"])

    def test_zero_hedge_risk_is_rejected(self) -> None:
        item = self.by_id["zeroHedgeRisk"]
        self.assertFalse(item["checks"]["domain_valid"])
        self.assertFalse(item["checks"]["result_bound"])
        self.assertIsNone(item["computed_result"])

    def test_relabelled_result_is_rejected(self) -> None:
        item = self.by_id["resultRelabeled"]
        self.assertFalse(item["checks"]["result_bound"])
        self.assertEqual(item["claimed_result"], [1, 2])
        self.assertEqual(item["computed_result"], [3, 4])

    def test_formula_hash_mismatch_is_rejected(self) -> None:
        item = self.by_id["formulaHashMismatch"]
        self.assertFalse(item["checks"]["definition_matched"])
        self.assertTrue(item["checks"]["result_bound"])

    def test_report_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["aggregate"]["valid_application_count"] = 7
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
