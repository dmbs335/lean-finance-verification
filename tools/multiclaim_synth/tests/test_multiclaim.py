from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.multiclaim_synth.errors import ValidationError
from tools.multiclaim_synth.model import load_problem
from tools.multiclaim_synth.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "examples" / "multiclaim" / "shared_attestation.json"


class MultiClaimSynthesisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.problem = load_problem(MODEL)
        self.report = solve(self.problem)

    def test_individual_minima_use_specialized_receipts(self) -> None:
        self.assertEqual(
            self.report["per_claim"]["noHidden"]["selected"]["channels"],
            ["hiddenReceipt"],
        )
        self.assertEqual(
            self.report["per_claim"]["noFuture"]["selected"]["channels"],
            ["futureReceipt"],
        )

    def test_shared_channel_beats_union_of_individual_minima(self) -> None:
        self.assertEqual(
            self.report["claim_specific_union"],
            {"channels": ["hiddenReceipt", "futureReceipt"], "cost": 4},
        )
        self.assertEqual(
            self.report["global"]["selected"]["channels"],
            ["unifiedAttestation"],
        )
        self.assertEqual(self.report["global"]["selected"]["cost"], 3)
        self.assertEqual(self.report["synergy_savings"], 1)

    def test_global_lower_cost_failures_are_constructive(self) -> None:
        for candidate in self.report["global"]["lower_cost_failures"]:
            self.assertFalse(candidate["verifies"])
            self.assertIn("uncovered", candidate)

    def test_tampered_report_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["synergy_savings"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.problem, tampered)

    def test_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.problem))


if __name__ == "__main__":
    unittest.main()
