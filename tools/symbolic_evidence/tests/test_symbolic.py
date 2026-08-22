from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.symbolic_evidence.errors import ValidationError
from tools.symbolic_evidence.model import load_corpus
from tools.symbolic_evidence.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "examples" / "attack_corpus" / "research_integrity.json"


class SymbolicEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = load_corpus(CORPUS)
        self.report = solve(self.corpus)

    def test_corpus_covers_twenty_attacks_and_seven_boundaries(self) -> None:
        self.assertEqual(self.report["attack_count"], 20)
        self.assertEqual(len(self.report["boundaries"]), 7)
        self.assertEqual(len(self.report["signature_classes"]), 12)

    def test_exact_optimum_uses_unified_and_external_time_evidence(self) -> None:
        self.assertEqual(self.report["selected"]["cost"], 10)
        self.assertIn(
            "unifiedIntegrityAttestation",
            self.report["selected"]["channels"],
        )
        self.assertTrue(
            {"transparencyLog", "tsaAnchor"}.intersection(
                self.report["selected"]["channels"]
            )
        )

    def test_every_attack_has_a_selected_separator(self) -> None:
        self.assertTrue(all(
            witness["selected_separators"]
            for witness in self.report["coverage_witnesses"]
        ))

    def test_branch_and_bound_prunes_the_exhaustive_space(self) -> None:
        search = self.report["search"]
        self.assertLess(
            search["explored_nodes"],
            search["exhaustive_candidate_count"],
        )

    def test_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["selected"]["cost"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.corpus, tampered)

    def test_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.corpus))


if __name__ == "__main__":
    unittest.main()
