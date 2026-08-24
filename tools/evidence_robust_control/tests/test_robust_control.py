from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.evidence_robust_control.errors import ValidationError
from tools.evidence_robust_control.model import load_problem
from tools.evidence_robust_control.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "evidence_robust_control" / "voi.json"


class EvidenceRobustControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)
        self.queries = {row["query"]: row for row in self.report["queries"]}

    def test_immediate_robust_policy_prefers_hold(self) -> None:
        selected = self.report["immediate_control"]["selected"]
        self.assertEqual(selected["action"], "hold")
        self.assertEqual(selected["robust_net_value_bps"], 1)

    def test_independent_query_has_positive_robust_value(self) -> None:
        query = self.queries["independentMacro"]
        self.assertEqual(query["post_query_guarantee_bps"], 4)
        self.assertEqual(query["net_post_query_value_bps"], 3)
        self.assertEqual(query["robust_value_of_information_bps"], 2)
        self.assertEqual(self.report["decision"]["kind"], "acquireEvidence")
        self.assertEqual(
            self.report["decision"]["selected_query"], "independentMacro"
        )

    def test_redundant_query_has_negative_value(self) -> None:
        query = self.queries["sameVendor"]
        self.assertEqual(query["net_post_query_value_bps"], 0)
        self.assertEqual(query["robust_value_of_information_bps"], -1)

    def test_observation_specific_robust_actions_change(self) -> None:
        outcomes = {
            row["observation"]: row
            for row in self.queries["independentMacro"]["outcomes"]
        }
        self.assertEqual(outcomes["stable"]["selected"]["action"], "increase")
        self.assertEqual(outcomes["stress"]["selected"]["action"], "reduce")

    def test_capital_expands_only_when_robust_gain_beats_crowding(self) -> None:
        rule = self.report["capital_rule"]
        self.assertEqual(rule["robust_gain_bps"], 2)
        self.assertEqual(rule["crowding_cost_increase_bps"], 1)
        self.assertTrue(rule["capital_increase_allowed"])

    def test_high_crowding_counterfactual_blocks_capital(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.json"
            raw = json.loads(MODEL.read_text(encoding="utf-8"))
            raw["capital_rule"]["crowding_cost_after_bps"] = 5
            path.write_text(json.dumps(raw), encoding="utf-8")
            report = solve(load_problem(path))
            self.assertFalse(report["capital_rule"]["capital_increase_allowed"])

    def test_unknown_model_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.json"
            raw = json.loads(MODEL.read_text(encoding="utf-8"))
            raw["queries"][0]["observations"]["stable"].append("unknown")
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "unknown model"):
                load_problem(path)

    def test_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["decision"]["kind"] = "actNow"
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
