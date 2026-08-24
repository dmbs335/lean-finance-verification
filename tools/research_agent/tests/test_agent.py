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
        self.assertIn(
            "certificate_composition", self.report["artifact_sha256"]
        )

    def test_all_seven_analysis_gates_pass(self) -> None:
        self.assertTrue(all(
            gate["passed"] for gate in self.report["gates"].values()
        ))
        self.assertTrue(
            self.report["gates"]["alpha_audit"]["exact_recovery"]
        )
        interval = self.report["gates"]["alpha_interval"]
        self.assertEqual(interval["interval_bps"], [30, 550])
        self.assertEqual(interval["interval_width_bps"], 520)
        self.assertEqual(
            self.report["gates"]["portfolio"]["adjusted_score_gain"],
            280,
        )
        self.assertEqual(
            self.report["gates"]["crowding"]["paradox_count"], 2
        )
        self.assertEqual(
            self.report["gates"]["liquidation"][
                "hidden_common_risk_pairs"
            ],
            1,
        )
        event = self.report["gates"]["event_study"]
        self.assertTrue(event["accepted_controlled"])
        self.assertEqual(event["average_event_did_bps"], 850)
        self.assertEqual(event["pair_count"], 3)
        composition = self.report["gates"]["composition"]
        self.assertTrue(composition["verifies_global_claim"])
        self.assertFalse(composition["local_summary_verifies"])
        self.assertEqual(
            composition["selected_channels"],
            [
                "dataDecisionBindingReceipt",
                "decisionResultBindingReceipt",
            ],
        )
        self.assertEqual(composition["selected_cost"], 4)
        self.assertEqual(composition["global_bundle_cost"], 6)

    def _modified_plan(self, mutate):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "plan.json"
        raw = json.loads(PLAN.read_text(encoding="utf-8"))
        mutate(raw)
        path.write_text(json.dumps(raw), encoding="utf-8")
        return temporary, run(load_plan(path, ROOT))

    def test_failed_portfolio_gate_refuses_certificate(self) -> None:
        temporary, report = self._modified_plan(
            lambda raw: raw["gates"].update(
                minimum_adjusted_portfolio_gain=1000
            )
        )
        try:
            self.assertEqual(report["status"], "rejected")
            self.assertIsNone(report["certificate"])
            self.assertFalse(report["gates"]["portfolio"]["passed"])
            self.assertEqual(
                report["completed_stages"],
                ["registered", "alphaAudited", "alphaBounded"],
            )
        finally:
            temporary.cleanup()

    def test_too_narrow_alpha_gate_refuses_certificate(self) -> None:
        temporary, report = self._modified_plan(
            lambda raw: raw["gates"].update(
                maximum_certifiable_interval_width_bps=500
            )
        )
        try:
            self.assertEqual(report["status"], "rejected")
            self.assertFalse(
                report["gates"]["alpha_interval"]["passed"]
            )
            self.assertEqual(
                report["completed_stages"],
                ["registered", "alphaAudited"],
            )
        finally:
            temporary.cleanup()

    def test_event_effect_gate_refuses_certificate(self) -> None:
        temporary, report = self._modified_plan(
            lambda raw: raw["gates"].update(
                minimum_event_study_average_did_bps=900
            )
        )
        try:
            self.assertEqual(report["status"], "rejected")
            self.assertIsNone(report["certificate"])
            self.assertFalse(report["gates"]["event_study"]["passed"])
            self.assertNotIn("eventStudied", report["completed_stages"])
            self.assertNotIn("pipelineComposed", report["completed_stages"])
            self.assertNotIn("certified", report["completed_stages"])
        finally:
            temporary.cleanup()

    def test_composition_cost_gate_refuses_certificate(self) -> None:
        temporary, report = self._modified_plan(
            lambda raw: raw["gates"].update(
                maximum_composition_evidence_cost=3
            )
        )
        try:
            self.assertEqual(report["status"], "rejected")
            self.assertIsNone(report["certificate"])
            composition = report["gates"]["composition"]
            self.assertTrue(composition["verifies_global_claim"])
            self.assertEqual(composition["selected_cost"], 4)
            self.assertFalse(composition["passed"])
            self.assertIn("eventStudied", report["completed_stages"])
            self.assertNotIn("pipelineComposed", report["completed_stages"])
            self.assertNotIn("certified", report["completed_stages"])
        finally:
            temporary.cleanup()

    def test_unsafe_analysis_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plan.json"
            raw = json.loads(PLAN.read_text(encoding="utf-8"))
            raw["analyses"]["certificate_composition"] = "../outside.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "inside repository"):
                load_plan(path, ROOT)

    def test_report_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["gates"]["composition"]["selected_cost"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.plan, tampered)

    def test_agent_is_deterministic(self) -> None:
        self.assertEqual(self.report, run(self.plan))


if __name__ == "__main__":
    unittest.main()
