from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.certificate_composition.errors import ValidationError
from tools.certificate_composition.model import load_problem
from tools.certificate_composition.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "certificate_composition" / "research_bundle.json"


class CertificateCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)

    def test_all_local_certificates_pass_but_local_summary_cannot_verify(self) -> None:
        self.assertTrue(
            self.report["local_certificates_all_valid_across_worlds"]
        )
        self.assertTrue(self.report["local_summary_constant_across_worlds"])
        local = self.report["local_summary_only"]
        self.assertFalse(local["verifies"])
        self.assertEqual(local["channels"], ["localValiditySummary"])
        self.assertIn(local["uncovered"]["left"], {"matched", "datasetSubstituted", "resultRelabeled", "bothSubstituted"})

    def test_exact_minimum_is_two_narrow_binding_receipts(self) -> None:
        selected = self.report["synthesis"]["selected"]
        self.assertEqual(
            selected["channels"],
            ["dataDecisionBindingReceipt", "decisionResultBindingReceipt"],
        )
        self.assertEqual(selected["cost"], 4)
        self.assertTrue(selected["verifies"])
        self.assertEqual(
            self.report["bridge_receipts_only"], selected
        )

    def test_global_bundle_works_but_is_more_expensive(self) -> None:
        global_bundle = self.report["global_bundle_only"]
        self.assertTrue(global_bundle["verifies"])
        self.assertEqual(global_bundle["channels"], ["globalBundleBinding"])
        self.assertEqual(global_bundle["cost"], 6)
        self.assertGreater(
            global_bundle["cost"],
            self.report["synthesis"]["selected"]["cost"],
        )

    def test_every_lower_cost_candidate_has_a_constructive_counterexample(self) -> None:
        failures = self.report["synthesis"]["lower_cost_failures"]
        self.assertTrue(failures)
        for candidate in failures:
            self.assertFalse(candidate["verifies"])
            self.assertIn("uncovered", candidate)
            self.assertTrue(candidate["uncovered"]["separators"])

    def test_disagreement_edges_require_both_bridge_classes(self) -> None:
        by_pair = {
            frozenset((edge["left"], edge["right"])): edge
            for edge in self.report["disagreement_edges"]
        }
        dataset_edge = by_pair[frozenset(("matched", "datasetSubstituted"))]
        result_edge = by_pair[frozenset(("matched", "resultRelabeled"))]
        self.assertIn("dataDecisionBindingReceipt", dataset_edge["separators"])
        self.assertNotIn("decisionResultBindingReceipt", dataset_edge["separators"])
        self.assertIn("decisionResultBindingReceipt", result_edge["separators"])
        self.assertNotIn("dataDecisionBindingReceipt", result_edge["separators"])

    def test_inconsistent_global_claim_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model.json"
            raw = json.loads(MODEL.read_text(encoding="utf-8"))
            raw["worlds"][1]["global_claim"] = True
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(
                ValidationError, "does not equal local claims and bindings"
            ):
                load_problem(path)

    def test_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["synthesis"]["selected"]["cost"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
