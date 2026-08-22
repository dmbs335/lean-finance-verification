from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.evidence_synth.canonical import canonical_bytes
from tools.evidence_synth.errors import ValidationError
from tools.robust_evidence_synth.lean import render_lean
from tools.robust_evidence_synth.model import load_model
from tools.robust_evidence_synth.solver import solve_model, verify_certificate

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = (
    REPOSITORY_ROOT
    / "examples"
    / "robust_evidence_synthesis"
    / "search_connectivity.json"
)
LEAN_PATH = (
    REPOSITORY_ROOT
    / "LeanFinance"
    / "Generated"
    / "RobustEvidenceSynthesis.lean"
)


class RobustEvidenceSynthesisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = load_model(MODEL_PATH)

    def test_exact_solver_finds_minimum_connectivity_two_portfolio(self) -> None:
        certificate = solve_model(self.model)
        self.assertEqual(certificate["status"], "synthesized")
        self.assertEqual(
            certificate["selected"]["channels"],
            [
                "selfReport",
                "declarationRegistry",
                "executorMirror",
                "executorB",
            ],
        )
        self.assertEqual(certificate["selected"]["weighted_cost"], 10)
        self.assertEqual(certificate["required_connectivity"], 2)

    def test_same_domain_mirror_does_not_count_as_independent(self) -> None:
        certificate = solve_model(self.model)
        hidden_edge = next(
            edge
            for edge in certificate["disagreement_edges"]
            if {edge["left"], edge["right"]}
            == {"honest", "hiddenSweep"}
        )
        self.assertEqual(
            hidden_edge["separator_domains"],
            ["executorA", "executorB"],
        )
        self.assertIn("executorA", hidden_edge["separators"])
        self.assertIn("executorMirror", hidden_edge["separators"])
        self.assertIn("executorB", hidden_edge["separators"])
        self.assertEqual(
            len(hidden_edge["separator_domains"]),
            2,
            "two channels in executorA remain one trust domain",
        )

    def test_independent_declaration_domain_is_also_required(self) -> None:
        certificate = solve_model(self.model)
        declaration_edge = next(
            edge
            for edge in certificate["disagreement_edges"]
            if {edge["left"], edge["right"]}
            == {"honest", "undeclaredBaseline"}
        )
        self.assertEqual(
            declaration_edge["separator_domains"],
            ["researcher", "registry"],
        )
        self.assertIn(
            "declarationRegistry", certificate["selected"]["channels"]
        )

    def test_fault_enumeration_contains_empty_and_every_single_domain(self) -> None:
        certificate = solve_model(self.model)
        self.assertEqual(
            certificate["faults"],
            [
                [],
                ["researcher"],
                ["registry"],
                ["executorA"],
                ["executorB"],
                ["tsa"],
            ],
        )

    def test_correlated_executor_domains_make_robust_verification_impossible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "correlated.json"
            raw = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
            for channel in raw["channels"]:
                if channel["id"] == "executorB":
                    channel["domain"] = "executorA"
            path.write_text(json.dumps(raw), encoding="utf-8")
            certificate = solve_model(load_model(path))
            self.assertEqual(certificate["status"], "impossible")
            self.assertEqual(
                certificate["impossibility_witness"]["separator_domains"],
                ["executorA"],
            )

    def test_every_lower_cost_candidate_has_fault_edge_witness(self) -> None:
        certificate = solve_model(self.model)
        edges = {
            edge["id"]: edge for edge in certificate["disagreement_edges"]
        }
        for candidate in certificate["lower_cost_failures"]:
            self.assertFalse(candidate["robust"])
            self.assertIn(candidate["uncovered_edge"], edges)
            self.assertIsInstance(candidate["failed_fault"], list)

    def test_certificate_tampering_is_rejected(self) -> None:
        certificate = solve_model(self.model)
        tampered = copy.deepcopy(certificate)
        tampered["selected"]["channels"] = ["executorMirror"]
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify_certificate(self.model, tampered)

    def test_generated_outputs_are_deterministic_and_typecheck(self) -> None:
        first = solve_model(self.model)
        second = solve_model(self.model)
        self.assertEqual(canonical_bytes(first), canonical_bytes(second))
        source = render_lean(self.model, first)
        self.assertEqual(source, render_lean(self.model, second))
        self.assertEqual(source, LEAN_PATH.read_text(encoding="utf-8"))
        self.assertNotIn("sorry", source.lower())
        result = subprocess.run(
            ["lake", "env", "lean", str(LEAN_PATH.relative_to(REPOSITORY_ROOT))],
            cwd=REPOSITORY_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=180,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg="generated robust Lean failed to typecheck:\n" + result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
