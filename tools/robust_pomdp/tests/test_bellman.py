from __future__ import annotations

import copy
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from tools.robust_pomdp.errors import ValidationError
from tools.robust_pomdp.model import load_problem
from tools.robust_pomdp.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "robust_pomdp" / "two_step.json"


class RobustPomdpBellmanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)
        self.horizon_one = self.report["layers"][1]["beliefs"]
        self.initial = self.report["layers"][2]["beliefs"]["uncertain"]

    @staticmethod
    def _as_fraction(value):
        return Fraction(value["numerator"], value["denominator"])

    def test_one_step_resolved_beliefs_select_robust_actions(self) -> None:
        self.assertEqual(self.horizon_one["stable"]["selected_action"], "increase")
        self.assertEqual(
            self._as_fraction(self.horizon_one["stable"]["robust_value_bps"]),
            Fraction(5, 1),
        )
        self.assertEqual(self.horizon_one["stress"]["selected_action"], "reduce")
        self.assertEqual(
            self._as_fraction(self.horizon_one["stress"]["robust_value_bps"]),
            Fraction(3, 1),
        )

    def test_two_step_initial_belief_selects_query(self) -> None:
        self.assertEqual(self.initial["selected_action"], "query")
        self.assertEqual(
            self._as_fraction(self.initial["robust_value_bps"]),
            Fraction(5, 2),
        )

    def test_query_model_values_are_exact(self) -> None:
        query = next(
            action for action in self.initial["actions"]
            if action["action"] == "query"
        )
        values = {
            row["model"]: self._as_fraction(row["q_value_bps"])
            for row in query["models"]
        }
        self.assertEqual(values, {
            "optimistic": Fraction(7, 2),
            "adverse": Fraction(5, 2),
        })
        self.assertEqual(query["worst_case_models"], ["adverse"])

    def test_immediate_hold_is_inferior_to_query(self) -> None:
        hold = next(
            action for action in self.initial["actions"]
            if action["action"] == "hold"
        )
        self.assertEqual(
            self._as_fraction(hold["robust_value_bps"]), Fraction(1, 1)
        )

    def test_unknown_successor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.json"
            raw = json.loads(MODEL.read_text(encoding="utf-8"))
            raw["beliefs"][0]["actions"][0]["transitions"]["adverse"][0]["next"] = "missing"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "unknown successor"):
                load_problem(path)

    def test_zero_branch_weight_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.json"
            raw = json.loads(MODEL.read_text(encoding="utf-8"))
            raw["beliefs"][0]["actions"][0]["transitions"]["adverse"][0]["weight"] = 0
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "positive"):
                load_problem(path)

    def test_tampered_report_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["initial_decision"]["action"] = "increase"
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
