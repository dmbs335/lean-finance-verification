from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.evidence_synth.canonical import canonical_bytes
from tools.evidence_synth.errors import ValidationError
from tools.evidence_synth.lean import render_lean
from tools.evidence_synth.model import load_model
from tools.evidence_synth.solver import solve_model, verify_certificate

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = REPOSITORY_ROOT / "examples" / "evidence_synthesis" / "search_completeness.json"


class EvidenceSynthesisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = load_model(MODEL_PATH)

    def test_exact_solver_finds_the_proved_minimal_search_evidence(self) -> None:
        certificate = solve_model(self.model)
        self.assertEqual(certificate["status"], "synthesized")
        self.assertEqual(
            certificate["selected"]["channels"],
            ["selfReport", "executorLog"],
        )
        self.assertEqual(certificate["selected"]["weighted_cost"], 7)
        self.assertEqual(
            [item["channels"] for item in certificate["minimal_verifying_sets"]],
            [["selfReport", "executorLog"]],
        )

    def test_cryptographic_postprocessing_channels_do_not_separate_hidden_trials(self) -> None:
        certificate = solve_model(self.model)
        edge = next(
            edge for edge in certificate["disagreement_edges"]
            if edge["left"] == "honest" and edge["right"] == "hiddenSweep"
        )
        self.assertEqual(edge["separators"], ["executorLog"])
        self.assertNotIn("resultBundle", edge["separators"])
        self.assertNotIn("rfc3161Anchor", edge["separators"])

    def test_every_lower_cost_candidate_contains_a_constructive_failure(self) -> None:
        certificate = solve_model(self.model)
        edges = {edge["id"]: edge for edge in certificate["disagreement_edges"]}
        for candidate in certificate["lower_cost_failures"]:
            self.assertFalse(candidate["verifies"])
            selected = set(candidate["channels"])
            edge = edges[candidate["uncovered_edge"]]
            self.assertTrue(selected.isdisjoint(edge["separators"]))

    def test_synthesis_is_byte_deterministic(self) -> None:
        first = solve_model(self.model)
        second = solve_model(self.model)
        self.assertEqual(canonical_bytes(first), canonical_bytes(second))
        self.assertEqual(render_lean(self.model, first), render_lean(self.model, second))

    def test_certificate_tampering_is_rejected(self) -> None:
        certificate = solve_model(self.model)
        tampered = copy.deepcopy(certificate)
        tampered["selected"]["channels"] = ["resultBundle"]
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify_certificate(self.model, tampered)

    def test_generated_lean_contains_checker_and_optimality_certificate(self) -> None:
        source = render_lean(self.model, solve_model(self.model))
        self.assertIn("def synthesisCertificate", source)
        self.assertIn("theorem cheaperCandidateCounterexample", source)
        self.assertIn("synthesized_selection_is_cost_minimal", source)
        self.assertNotIn("sorry", source.lower())

    def test_empty_separator_produces_impossibility_witness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "impossible.json"
            raw = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
            for channel in raw["channels"]:
                channel["observations"]["hiddenSweep"] = channel["observations"]["honest"]
            path.write_text(json.dumps(raw), encoding="utf-8")
            model = load_model(path)
            certificate = solve_model(model)
            self.assertEqual(certificate["status"], "impossible")
            self.assertEqual(certificate["impossibility_witness"]["separators"], [])
            source = render_lean(model, certificate)
            self.assertIn("all_channels_cannot_verify", source)

    def test_model_rejects_unbounded_exact_search(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "too-many.json"
            raw = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
            prototype = raw["channels"][0]
            raw["channels"] = []
            for index in range(13):
                channel = copy.deepcopy(prototype)
                channel["id"] = f"channel-{index}"
                raw["channels"].append(channel)
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "at most 12"):
                load_model(path)


if __name__ == "__main__":
    unittest.main()
