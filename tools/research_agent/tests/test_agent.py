from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.research_agent.errors import ValidationError
from tools.research_agent.model import load_plan
from tools.research_agent.runner import STAGES, run, verify

ROOT = Path(__file__).resolve().parents[3]
PLAN = ROOT / "examples" / "research_agent" / "plan.json"


class ResearchAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = load_plan(PLAN, ROOT)
        self.report = run(self.plan)

    def test_end_to_end_plan_emits_bounded_certificate(self) -> None:
        self.assertEqual(self.report["status"], "certified-bounded")
        self.assertEqual(self.report["completed_stages"], STAGES)
        self.assertIsNotNone(self.report["certificate"])
        self.assertEqual(
            self.report["certificate"]["plan_sha256"],
            self.report["plan_sha256"],
        )

    def test_all_four_analysis_gates_pass(self) -> None:
        self.assertTrue(all(
            gate["passed"] for gate in self.report["gates"].values()
        ))
        self.assertTrue(self.report["gates"]["alpha_audit"]["exact_recovery"])
        self.assertEqual(
            self.report["gates"]["portfolio"]["adjusted_score_gain"], 280
        )
        self.assertEqual(self.report["gates"]["crowding"]["paradox_count"], 2)
        self.assertEqual(
            self.report["gates"]["liquidation"]["hidden_common_risk_pairs"], 1
        )

    def test_failed_gate_refuses_certificate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plan.json"
            raw = json.loads(PLAN.read_text(encoding="utf-8"))
            raw["gates"]["minimum_adjusted_portfolio_gain"] = 1000
            path.write_text(json.dumps(raw), encoding="utf-8")
            report = run(load_plan(path, ROOT))
            self.assertEqual(report["status"], "rejected")
            self.assertIsNone(report["certificate"])
            self.assertFalse(report["gates"]["portfolio"]["passed"])
            self.assertNotIn("certified", report["completed_stages"])

    def test_unsafe_analysis_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plan.json"
            raw = json.loads(PLAN.read_text(encoding="utf-8"))
            raw["analyses"]["fake_alpha_benchmark"] = "../outside.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "inside repository"):
                load_plan(path, ROOT)

    def test_report_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["status"] = "rejected"
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.plan, tampered)

    def test_agent_is_deterministic(self) -> None:
        self.assertEqual(self.report, run(self.plan))


if __name__ == "__main__":
    unittest.main()
