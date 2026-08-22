from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.trace_refinement.build import build
from tools.trace_refinement.errors import ValidationError
from tools.trace_refinement.refine import verify_refinement_report
from tools.workflow_cegis.canonical import canonical_bytes

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
BASE_MODEL = (
    REPOSITORY_ROOT
    / "examples"
    / "workflow_cegis"
    / "search_integrity.json"
)
TRACE = (
    REPOSITORY_ROOT
    / "examples"
    / "trace_refinement"
    / "cost_model_tampering.trace.json"
)


class TraceRefinementTests(unittest.TestCase):
    def test_unknown_event_extends_state_action_and_claim_semantics(self) -> None:
        result = build(BASE_MODEL, TRACE)
        variable_ids = [item["id"] for item in result.refined_model_raw["variables"]]
        action_ids = [item["id"] for item in result.refined_model_raw["actions"]]
        self.assertIn("costModelTampered", variable_ids)
        self.assertIn("tamperCostModel", action_ids)
        self.assertEqual(
            result.report["original_failure"],
            {
                "step_index": 2,
                "event": "tamperCostModel",
                "reason": "unknown_action",
            },
        )
        self.assertEqual(len(result.report["refinement_iterations"]), 1)
        refinement = result.report["refinement_iterations"][0]
        self.assertEqual(
            refinement["state_delta"], {"costModelTampered": True}
        )
        self.assertIn(
            {"not": {"var": "costModelTampered"}},
            result.refined_model_raw["claim"]["all"],
        )

    def test_refined_model_reproduces_observed_attack_as_violation(self) -> None:
        result = build(BASE_MODEL, TRACE)
        replay = result.report["refined_replay"]
        self.assertTrue(replay["terminal"])
        self.assertFalse(replay["claim"])
        self.assertTrue(replay["final_state"]["costModelTampered"])
        history_ids = {
            item["id"]
            for item in result.workflow.report["exploration"]["histories"]
        }
        self.assertIn("costModelTampering", history_ids)
        self.assertEqual(
            result.workflow.report["exploration"]["history_count"], 32
        )

    def test_new_separator_basis_is_resynthesized(self) -> None:
        result = build(BASE_MODEL, TRACE)
        analysis = result.report["separator_analysis"]
        self.assertEqual(
            analysis["separator_basis"],
            ["targetedReceipt_tamperCostModel"],
        )
        self.assertEqual(
            analysis["minimum_repair"],
            [
                "targetedReceipt_executeHiddenSweep",
                "targetedReceipt_readFutureData",
                "targetedReceipt_tamperCostModel",
            ],
        )
        self.assertEqual(
            analysis["greenfield_selection"],
            [
                "selfReport",
                "targetedReceipt_executeHiddenSweep",
                "targetedReceipt_readFutureData",
                "targetedReceipt_tamperCostModel",
            ],
        )

    def test_full_executor_log_does_not_cover_control_plane_mutation(self) -> None:
        result = build(BASE_MODEL, TRACE)
        edges = result.report["separator_analysis"]["honest_attack_edges"]
        self.assertEqual(len(edges), 1)
        separators = edges[0]["separators"]
        self.assertNotIn("fullExecutorLog", separators)
        self.assertNotIn("resultBundle", separators)
        self.assertNotIn("rfc3161Anchor", separators)
        self.assertIn("targetedReceipt_tamperCostModel", separators)

    def test_refinement_and_generated_lean_are_deterministic(self) -> None:
        first = build(BASE_MODEL, TRACE)
        second = build(BASE_MODEL, TRACE)
        self.assertEqual(
            canonical_bytes(first.refined_model_raw),
            canonical_bytes(second.refined_model_raw),
        )
        self.assertEqual(canonical_bytes(first.report), canonical_bytes(second.report))
        self.assertEqual(first.workflow.workflow_lean, second.workflow.workflow_lean)
        self.assertEqual(first.workflow.evidence_lean, second.workflow.evidence_lean)
        self.assertEqual(first.workflow.bridge_lean, second.workflow.bridge_lean)
        self.assertEqual(first.trace_lean, second.trace_lean)
        self.assertIn("def refinementCertificate", first.trace_lean)
        self.assertIn("original_model_has_action_alphabet_gap", first.trace_lean)
        self.assertIn(
            "refined_separator_basis_distinguishes_observed_attack",
            first.trace_lean,
        )
        self.assertNotIn("sorry", first.trace_lean.lower())

    def test_report_tampering_is_rejected(self) -> None:
        result = build(BASE_MODEL, TRACE)
        tampered = copy.deepcopy(result.report)
        tampered["separator_analysis"]["separator_basis"] = ["rfc3161Anchor"]
        with self.assertRaisesRegex(ValidationError, "exact regeneration"):
            verify_refinement_report(BASE_MODEL, TRACE, tampered)

    def test_unknown_event_without_state_delta_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing-delta.json"
            raw = json.loads(TRACE.read_text(encoding="utf-8"))
            unknown = raw["steps"][2]
            unknown["observed_after"] = {
                "costModelTampered": False
            }
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "no observed state delta"):
                build(BASE_MODEL, path)

    def test_already_reproducible_trace_does_not_claim_refinement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "known-only.json"
            raw = json.loads(TRACE.read_text(encoding="utf-8"))
            raw["id"] = "knownOnly"
            raw["variable_extensions"] = []
            raw["steps"] = [
                {"event": "declareBaseline"},
                {"event": "executeBaseline"},
                {"event": "publishResult"},
                {"event": "anchorLedger"},
            ]
            raw["expected_claim"] = True
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "no model refinement"):
                build(BASE_MODEL, path)


if __name__ == "__main__":
    unittest.main()
