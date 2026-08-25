from __future__ import annotations

import copy
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from tools.mcts_spibb.errors import ValidationError
from tools.mcts_spibb.model import load_plan
from tools.mcts_spibb.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
PLAN = ROOT / "examples" / "mcts_spibb" / "planner.json"


class MctsSpibbPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = load_plan(PLAN, ROOT)
        self.report = solve(self.plan)

    @staticmethod
    def _fraction(value):
        return Fraction(value["numerator"], value["denominator"])

    def _modified(self, mutate):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "plan.json"
        raw = json.loads(PLAN.read_text(encoding="utf-8"))
        mutate(raw)
        path.write_text(json.dumps(raw), encoding="utf-8")
        return temporary, solve(load_plan(path, ROOT))

    def test_tree_expands_only_hold_and_supported_query_at_root(self) -> None:
        search = self.report["search"]
        self.assertEqual(search["allowed_actions"], ["hold", "query"])
        excluded = {
            row["action"]: row["reasons"]
            for row in search["excluded_actions"]
        }
        self.assertEqual(excluded["increase"], ["insufficientSupport"])
        self.assertEqual(excluded["reduce"], ["insufficientSupport"])

    def test_bounded_search_proposes_query(self) -> None:
        search = self.report["search"]
        self.assertEqual(search["proposal"], "query")
        visits = {
            row["action"]: row["visits"]
            for row in search["root_statistics"]
        }
        self.assertEqual(sum(visits.values()), 128)
        self.assertGreater(visits["query"], visits["hold"])

    def test_exact_gate_accepts_query_over_baseline(self) -> None:
        gate = self.report["exact_root_gate"]
        self.assertEqual(gate["baseline_action"], "hold")
        self.assertEqual(gate["proposal_action"], "query")
        self.assertEqual(
            self._fraction(gate["baseline_robust_value_bps"]),
            Fraction(1, 1),
        )
        self.assertEqual(
            self._fraction(gate["proposal_robust_value_bps"]),
            Fraction(5, 2),
        )
        self.assertTrue(gate["passed"])
        self.assertEqual(gate["selected_action"], "query")

    def test_unsupported_query_forces_baseline_search(self) -> None:
        temporary, report = self._modified(
            lambda raw: raw["support_counts"]["uncertain"].update(query=2)
        )
        try:
            self.assertEqual(report["search"]["allowed_actions"], ["hold"])
            self.assertEqual(report["search"]["proposal"], "hold")
            self.assertEqual(
                report["exact_root_gate"]["selected_action"], "hold"
            )
        finally:
            temporary.cleanup()

    def test_unsafe_query_forces_baseline_search(self) -> None:
        temporary, report = self._modified(
            lambda raw: raw["safe_actions"]["uncertain"].remove("query")
        )
        try:
            self.assertEqual(report["search"]["allowed_actions"], ["hold"])
            self.assertEqual(report["search"]["proposal"], "hold")
        finally:
            temporary.cleanup()

    def test_stricter_exact_margin_overrides_mcts(self) -> None:
        temporary, report = self._modified(
            lambda raw: raw.update(required_root_margin_bps=2)
        )
        try:
            self.assertEqual(report["search"]["proposal"], "query")
            self.assertFalse(report["exact_root_gate"]["passed"])
            self.assertEqual(
                report["exact_root_gate"]["selected_action"], "hold"
            )
        finally:
            temporary.cleanup()

    def test_unsafe_repository_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plan.json"
            raw = json.loads(PLAN.read_text(encoding="utf-8"))
            raw["robust_model"] = "../outside.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "inside repository"):
                load_plan(path, ROOT)

    def test_tampered_report_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["exact_root_gate"]["selected_action"] = "increase"
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.plan, tampered)

    def test_planner_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.plan))


if __name__ == "__main__":
    unittest.main()
