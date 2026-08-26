from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.formula_contract.errors import ValidationError
from tools.formula_contract.model import NARROW_RECEIPTS, load_problem
from tools.formula_contract.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "formula_contract" / "hedge_scale.json"


class FormulaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)
        self.worlds = {
            world["id"]: world for world in self.report["worlds"]
        }

    def test_formula_validity_alone_does_not_verify_application(self) -> None:
        formula_only = self.report["formula_validity_only"]
        self.assertEqual(formula_only["channels"], ["formulaValiditySummary"])
        self.assertFalse(formula_only["verifies"])
        self.assertTrue(formula_only["uncovered"]["separators"])

    def test_exact_minimum_is_six_narrow_application_receipts(self) -> None:
        selected = self.report["synthesis"]["selected"]
        self.assertEqual(selected["channels"], list(NARROW_RECEIPTS))
        self.assertEqual(selected["cost"], 6)
        self.assertTrue(selected["verifies"])
        self.assertEqual(self.report["narrow_receipts_only"], selected)

    def test_global_application_bundle_works_but_costs_more(self) -> None:
        global_bundle = self.report["global_bundle_only"]
        self.assertTrue(global_bundle["verifies"])
        self.assertEqual(global_bundle["channels"], ["globalApplicationBinding"])
        self.assertEqual(global_bundle["cost"], 8)
        self.assertGreater(
            global_bundle["cost"],
            self.report["synthesis"]["selected"]["cost"],
        )

    def test_each_invalid_world_breaks_exactly_one_application_dimension(self) -> None:
        expected = {
            "unitMismatch": "units_valid",
            "futureInput": "temporally_available",
            "zeroDenominator": "domain_satisfied",
            "implementationDrift": "implementation_bound",
            "inputSubstituted": "inputs_bound",
            "outputRelabeled": "output_bound",
        }
        self.assertTrue(
            self.worlds["correct"]["properties"]["application_claim"]
        )
        for world_id, failed_property in expected.items():
            properties = self.worlds[world_id]["properties"]
            self.assertFalse(properties["application_claim"])
            failed = {
                key
                for key, value in properties.items()
                if key != "application_claim" and not value
            }
            self.assertEqual(failed, {failed_property})
            self.assertTrue(properties["formula_valid"])

    def test_every_lower_cost_candidate_has_a_counterexample(self) -> None:
        failures = self.report["synthesis"]["lower_cost_failures"]
        self.assertTrue(failures)
        for candidate in failures:
            self.assertFalse(candidate["verifies"])
            self.assertIn("uncovered", candidate)
            self.assertTrue(candidate["uncovered"]["separators"])

    def test_candidate_space_is_exhaustive(self) -> None:
        self.assertEqual(self.report["channel_count"], 8)
        self.assertEqual(self.report["candidate_count"], 256)
        self.assertEqual(self.report["world_count"], 7)

    def test_inconsistent_formula_input_set_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.json"
            raw = json.loads(MODEL.read_text(encoding="utf-8"))
            del raw["worlds"][0]["inputs"]["hedgeRisk"]
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(
                ValidationError, "keys must match formula inputs"
            ):
                load_problem(path)

    def test_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["synthesis"]["selected"]["cost"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
