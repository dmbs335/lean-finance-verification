from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.evidence_taxonomy.analyze import analyze, verify_report
from tools.evidence_taxonomy.canonical import canonical_bytes
from tools.evidence_taxonomy.errors import ValidationError

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SPEC = (
    REPOSITORY_ROOT
    / "examples"
    / "evidence_taxonomy"
    / "cost_model_novelty.json"
)


class EvidenceTaxonomyTests(unittest.TestCase):
    def test_cost_model_tampering_is_a_new_observation_boundary(self) -> None:
        report = analyze(SPEC)
        candidate = next(
            item
            for item in report["candidate_novelty"]
            if item["attack"] == "costModelTampering"
        )
        self.assertEqual(
            candidate["separators"],
            ["targetedReceipt_tamperCostModel"],
        )
        self.assertEqual(candidate["classification"], "new_observation_boundary")
        self.assertTrue(candidate["exact_signature_novel"])
        self.assertFalse(candidate["basis_covered"])
        self.assertTrue(candidate["unique_separator"])
        self.assertEqual(
            candidate["unseen_separators"],
            ["targetedReceipt_tamperCostModel"],
        )

    def test_reordered_dual_attack_reuses_an_existing_class(self) -> None:
        report = analyze(SPEC)
        candidate = next(
            item
            for item in report["candidate_novelty"]
            if item["attack"] == "history16"
        )
        self.assertEqual(candidate["classification"], "existing_class")
        self.assertEqual(candidate["equivalent_known_attacks"], ["dualAttack"])
        attack_rows = {item["attack"]: item for item in report["attacks"]}
        self.assertEqual(
            attack_rows["history16"]["class_id"],
            attack_rows["dualAttack"]["class_id"],
        )

    def test_hidden_signature_is_stricter_than_dual_signature(self) -> None:
        report = analyze(SPEC)
        attack_rows = {item["attack"]: item for item in report["attacks"]}
        relation = {
            (item["stricter_class"], item["broader_class"])
            for item in report["strict_signature_subsumption"]
        }
        self.assertIn(
            (
                attack_rows["hiddenSweep"]["class_id"],
                attack_rows["dualAttack"]["class_id"],
            ),
            relation,
        )

    def test_taxonomy_is_byte_deterministic(self) -> None:
        self.assertEqual(canonical_bytes(analyze(SPEC)), canonical_bytes(analyze(SPEC)))

    def test_report_tampering_is_rejected(self) -> None:
        report = analyze(SPEC)
        tampered = copy.deepcopy(report)
        tampered["candidate_novelty"][0]["classification"] = "existing_class"
        with self.assertRaisesRegex(ValidationError, "exact regeneration"):
            verify_report(SPEC, tampered)

    def test_unknown_catalog_history_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid.json"
            raw = json.loads(SPEC.read_text(encoding="utf-8"))
            raw["evidence_model"] = str(
                (
                    REPOSITORY_ROOT
                    / "examples"
                    / "trace_refinement"
                    / "generated"
                    / "evidence-model.canonical.json"
                ).resolve()
            )
            raw["known_attacks"].append("not-a-history")
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "unknown history"):
                analyze(path)


if __name__ == "__main__":
    unittest.main()
