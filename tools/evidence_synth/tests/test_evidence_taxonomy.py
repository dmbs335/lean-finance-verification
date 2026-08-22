from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.evidence_synth.canonical import canonical_bytes
from tools.evidence_synth.errors import ValidationError
from tools.evidence_synth.model import load_model
from tools.evidence_taxonomy.config import load_config
from tools.evidence_taxonomy.solver import solve_taxonomy, verify_report

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = (
    REPOSITORY_ROOT
    / "examples"
    / "trace_refinement"
    / "generated"
    / "evidence-model.canonical.json"
)
CONFIG_PATH = (
    REPOSITORY_ROOT
    / "examples"
    / "evidence_taxonomy"
    / "research_integrity.json"
)


class EvidenceTaxonomyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = load_model(MODEL_PATH)
        self.config = load_config(CONFIG_PATH)
        self.report = solve_taxonomy(self.model, self.config)

    def attack(self, attack_id: str) -> dict:
        return next(
            attack
            for attack in self.report["attacks"]
            if attack["id"] == attack_id
        )

    def test_controlled_corpus_forms_five_distinct_obligation_classes(self) -> None:
        self.assertEqual(len(self.report["classes"]), 5)
        class_ids = {
            attack["id"]: attack["class_id"]
            for attack in self.report["attacks"]
        }
        self.assertEqual(len(set(class_ids.values())), 5)

    def test_unique_control_plane_separator_is_required(self) -> None:
        tampering = self.attack("costModelTampering")
        self.assertEqual(
            tampering["required_channels"],
            ["targetedReceipt_tamperCostModel"],
        )
        separators = tampering["separator_edges"][0]["separators"]
        self.assertNotIn("fullExecutorLog", separators)
        self.assertNotIn("resultBundle", separators)
        self.assertNotIn("rfc3161Anchor", separators)
        self.assertEqual(separators, ["targetedReceipt_tamperCostModel"])

    def test_hidden_and_future_atomic_obligations_subsume_dual_attack(self) -> None:
        subsumptions = {
            (item["stronger"], item["weaker"])
            for item in self.report["subsumptions"]
        }
        self.assertIn(("hiddenSweep", "dualAttack"), subsumptions)
        self.assertIn(("futureLeak", "dualAttack"), subsumptions)

    def test_dual_attack_adds_no_marginal_evidence_debt(self) -> None:
        debt = {
            item["attack"]: item
            for item in self.report["evidence_debt_trace"]
        }
        self.assertEqual(debt["undeclaredBaseline"]["new_cost"], 2)
        self.assertEqual(debt["hiddenSweep"]["new_cost"], 4)
        self.assertEqual(debt["futureLeak"]["new_cost"], 6)
        self.assertEqual(debt["costModelTampering"]["new_cost"], 8)
        self.assertEqual(debt["dualAttack"]["new_cost"], 8)
        self.assertEqual(debt["dualAttack"]["marginal_debt"], 0)

    def test_each_atomic_boundary_has_two_unit_minimum_cost(self) -> None:
        for attack_id in (
            "undeclaredBaseline",
            "hiddenSweep",
            "futureLeak",
            "costModelTampering",
            "dualAttack",
        ):
            self.assertEqual(self.attack(attack_id)["minimum_cost"], 2)

    def test_taxonomy_is_byte_deterministic(self) -> None:
        second = solve_taxonomy(self.model, self.config)
        self.assertEqual(canonical_bytes(self.report), canonical_bytes(second))

    def test_report_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["attacks"][0]["class_id"] = "invented-class"
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify_report(self.model, self.config, tampered)


if __name__ == "__main__":
    unittest.main()
