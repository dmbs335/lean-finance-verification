from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.workflow_cegis.build import build
from tools.workflow_cegis.canonical import canonical_bytes
from tools.workflow_cegis.engine import run_cegis, verify_report
from tools.workflow_cegis.errors import ValidationError
from tools.workflow_cegis.explore import expand_channels, explore_histories
from tools.workflow_cegis.model import load_model

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = (
    REPOSITORY_ROOT
    / "examples"
    / "workflow_cegis"
    / "search_integrity.json"
)


class WorkflowCegisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = load_model(MODEL_PATH)
        self.histories = explore_histories(self.model)
        self.channels = expand_channels(self.model)

    def test_transition_system_generates_complete_bounded_attack_catalog(self) -> None:
        self.assertEqual(len(self.histories), 10)
        by_id = {history.id: history for history in self.histories}
        self.assertTrue(by_id["honest"].claim)
        for attack in (
            "undeclaredBaseline",
            "hiddenSweep",
            "futureLeak",
            "dualAttack",
        ):
            self.assertFalse(by_id[attack].claim)
        self.assertEqual(
            by_id["dualAttack"].trace,
            (
                "declareBaseline",
                "executeBaseline",
                "executeHiddenSweep",
                "readFutureData",
                "publishResult",
                "anchorLedger",
            ),
        )

    def test_sensor_templates_generate_targeted_receipts(self) -> None:
        by_id = {channel.id: channel for channel in self.channels}
        self.assertEqual(len(self.channels), 6)
        self.assertIn("targetedReceipt_executeHiddenSweep", by_id)
        self.assertIn("targetedReceipt_readFutureData", by_id)
        self.assertFalse(by_id["targetedReceipt_executeHiddenSweep"].deployed)
        self.assertEqual(
            by_id["targetedReceipt_executeHiddenSweep"].visible_actions,
            ("executeHiddenSweep",),
        )

    def test_cegis_discovers_atomic_gaps_and_converges(self) -> None:
        report = run_cegis(self.model)
        self.assertEqual(report["refinement_status"], "synthesized")
        self.assertEqual(
            [round_["status"] for round_ in report["iterations"]],
            ["counterexample", "counterexample", "verified"],
        )
        first, second = report["iterations"][:2]
        self.assertEqual(
            {first["counterexample"]["left"], first["counterexample"]["right"]},
            {"honest", "futureLeak"},
        )
        self.assertEqual(
            {second["counterexample"]["left"], second["counterexample"]["right"]},
            {"honest", "hiddenSweep"},
        )
        self.assertEqual(
            report["newly_required_channels"],
            [
                "targetedReceipt_executeHiddenSweep",
                "targetedReceipt_readFutureData",
            ],
        )

    def test_exact_repair_prefers_narrow_receipts_to_full_executor_log(self) -> None:
        report = run_cegis(self.model)
        repair = report["exact_repair_synthesis"]
        self.assertEqual(repair["status"], "synthesized")
        self.assertEqual(
            repair["selected"]["optional_channels"],
            [
                "targetedReceipt_executeHiddenSweep",
                "targetedReceipt_readFutureData",
            ],
        )
        self.assertEqual(
            repair["selected"]["incremental_weighted_cost"], 4
        )
        full_log = next(
            candidate
            for candidate in repair["minimal_repairs"]
            if candidate["optional_channels"] == ["fullExecutorLog"]
        )
        self.assertEqual(full_log["incremental_weighted_cost"], 6)

    def test_global_optimum_discards_postprocessing_channels_for_this_claim(self) -> None:
        report = run_cegis(self.model)
        global_selection = report["exact_synthesis"]["selected"]["channels"]
        self.assertEqual(
            global_selection,
            [
                "selfReport",
                "targetedReceipt_executeHiddenSweep",
                "targetedReceipt_readFutureData",
            ],
        )
        self.assertEqual(
            report["deployment_analysis"]["deployed_but_globally_redundant"],
            ["resultBundle", "rfc3161Anchor"],
        )

    def test_visible_bundle_and_timestamp_do_not_separate_hidden_actions(self) -> None:
        report = run_cegis(self.model)
        edges = report["exact_synthesis"]["disagreement_edges"]
        hidden = next(
            edge for edge in edges
            if {edge["left"], edge["right"]} == {"honest", "hiddenSweep"}
        )
        future = next(
            edge for edge in edges
            if {edge["left"], edge["right"]} == {"honest", "futureLeak"}
        )
        for edge in (hidden, future):
            self.assertNotIn("resultBundle", edge["separators"])
            self.assertNotIn("rfc3161Anchor", edge["separators"])
        self.assertIn("targetedReceipt_executeHiddenSweep", hidden["separators"])
        self.assertIn("targetedReceipt_readFutureData", future["separators"])

    def test_report_and_generated_lean_are_deterministic(self) -> None:
        first = build(MODEL_PATH)
        second = build(MODEL_PATH)
        self.assertEqual(canonical_bytes(first.report), canonical_bytes(second.report))
        self.assertEqual(first.workflow_lean, second.workflow_lean)
        self.assertEqual(first.evidence_lean, second.evidence_lean)
        self.assertEqual(first.bridge_lean, second.bridge_lean)
        for source in (first.workflow_lean, first.evidence_lean, first.bridge_lean):
            self.assertNotIn("sorry", source.lower())
        self.assertIn("generated_traces_complete", first.workflow_lean)
        self.assertIn("def proofCarryingCEGIS", first.bridge_lean)
        self.assertIn("refined_selection_is_minimum_cost_repair", first.bridge_lean)

    def test_report_tampering_is_rejected(self) -> None:
        report = run_cegis(self.model)
        tampered = copy.deepcopy(report)
        tampered["newly_required_channels"] = ["fullExecutorLog"]
        with self.assertRaisesRegex(ValidationError, "exact regeneration"):
            verify_report(self.model, tampered)

    def test_missing_sensor_language_reports_unresolved_gap_and_suggestions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "no-repair.json"
            raw = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
            raw["channels"] = [
                channel
                for channel in raw["channels"]
                if channel["deployed"]
            ]
            raw["sensor_templates"] = []
            path.write_text(json.dumps(raw), encoding="utf-8")
            model = load_model(path)
            report = run_cegis(model)
            self.assertEqual(report["refinement_status"], "unresolved")
            suggestions = report["failure"]["primitive_sensor_suggestions"]
            targets = {item["target"] for item in suggestions}
            self.assertTrue(
                {"executeHiddenSweep", "readFutureData"}.intersection(targets)
            )

    def test_refinement_budget_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "budget.json"
            raw = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
            raw["max_refinements"] = 1
            path.write_text(json.dumps(raw), encoding="utf-8")
            model = load_model(path)
            report = run_cegis(model)
            self.assertEqual(report["refinement_status"], "unresolved")
            self.assertEqual(report["failure"]["reason"], "refinement budget exhausted")

    def test_expanded_channel_bound_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "too-many.json"
            raw = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
            prototype = raw["channels"][0]
            for index in range(7):
                channel = copy.deepcopy(prototype)
                channel["id"] = f"extra-{index}"
                channel["deployed"] = False
                raw["channels"].append(channel)
            path.write_text(json.dumps(raw), encoding="utf-8")
            model = load_model(path)
            with self.assertRaisesRegex(ValidationError, "exceeds 12 channels"):
                expand_channels(model)


if __name__ == "__main__":
    unittest.main()
