from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.safe_tree_search.errors import ValidationError
from tools.safe_tree_search.model import load_problem
from tools.safe_tree_search.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "safe_tree_search" / "controlled.json"


class SafeTreePolicySearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)

    def _state(self, horizon: int, state: str) -> dict:
        layer = next(
            item for item in self.report["layers"]
            if item["remaining_horizon"] == horizon
        )
        return next(item for item in layer["states"] if item["state"] == state)

    def _counterfactual(self, mutate):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "model.json"
        raw = json.loads(MODEL.read_text(encoding="utf-8"))
        mutate(raw)
        path.write_text(json.dumps(raw), encoding="utf-8")
        return temporary, load_problem(path)

    def test_one_step_gain_is_rejected_by_longer_robust_horizon(self) -> None:
        self.assertEqual(self._state(1, "normal")["selected_action"], "increase")
        self.assertEqual(self._state(2, "normal")["selected_action"], "hold")
        self.assertEqual(self._state(3, "normal")["selected_action"], "hold")
        self.assertEqual(self.report["root_decision"]["action"], "hold")
        self.assertTrue(self.report["root_decision"]["is_baseline"])

    def test_root_pessimistic_value_is_exact(self) -> None:
        value = self.report["root_decision"]["pessimistic_lower_value"]
        self.assertEqual(value["numerator"], 157)
        self.assertEqual(value["denominator"], 40)

    def test_unsupported_high_reward_action_is_never_expanded(self) -> None:
        normal = self._state(1, "normal")
        leverage = next(
            action for action in normal["actions"]
            if action["action"] == "leverage"
        )
        self.assertTrue(leverage["safe"])
        self.assertFalse(leverage["supported"])
        self.assertFalse(leverage["admissible"])
        self.assertEqual(leverage["excluded_reason"], "insufficient-support")

    def test_unsafe_action_is_never_selected_despite_reward(self) -> None:
        normal = self._state(1, "normal")
        jump = next(
            action for action in normal["actions"]
            if action["action"] == "jump"
        )
        self.assertEqual(jump["immediate_reward_lcb"], 30)
        self.assertFalse(jump["admissible"])
        self.assertEqual(jump["excluded_reason"], "unsafe")
        self.assertTrue(
            self.report["controlled_claims"]["unsafe_actions_never_selected"]
        )

    def test_zero_support_baseline_remains_total(self) -> None:
        ruin = self._state(1, "ruin")
        hold = ruin["actions"][0]
        self.assertEqual(hold["support_count"], 0)
        self.assertTrue(hold["baseline"])
        self.assertTrue(hold["admissible"])
        self.assertEqual(ruin["selected_action"], "hold")
        self.assertTrue(self.report["controlled_claims"]["baseline_is_total"])

    def test_support_counterfactual_falls_back_at_one_step(self) -> None:
        def mutate(raw):
            normal = next(
                state for state in raw["states"] if state["id"] == "normal"
            )
            increase = next(
                action for action in normal["actions"]
                if action["id"] == "increase"
            )
            increase["support_count"] = 2

        temporary, problem = self._counterfactual(mutate)
        try:
            report = solve(problem)
            layer = next(
                item for item in report["layers"]
                if item["remaining_horizon"] == 1
            )
            normal = next(
                item for item in layer["states"] if item["state"] == "normal"
            )
            self.assertEqual(normal["selected_action"], "hold")
            self.assertTrue(normal["selected_is_baseline"])
        finally:
            temporary.cleanup()

    def test_unsafe_baseline_is_rejected_at_parse_time(self) -> None:
        def mutate(raw):
            stressed = next(
                state for state in raw["states"] if state["id"] == "stressed"
            )
            reduce = next(
                action for action in stressed["actions"]
                if action["id"] == "reduce"
            )
            reduce["safe"] = False

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.json"
            raw = json.loads(MODEL.read_text(encoding="utf-8"))
            mutate(raw)
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "baseline action"):
                load_problem(path)

    def test_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["root_decision"]["action"] = "leverage"
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
