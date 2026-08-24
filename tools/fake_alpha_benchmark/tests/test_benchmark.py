from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.fake_alpha_benchmark.errors import ValidationError
from tools.fake_alpha_benchmark.model import load_benchmark
from tools.fake_alpha_benchmark.solver import solve, verify

ROOT = Path(__file__).resolve().parents[3]
BENCHMARK = ROOT / "examples" / "fake_alpha" / "controlled.json"


class FakeAlphaBenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.benchmark = load_benchmark(BENCHMARK)
        self.report = solve(self.benchmark)

    def test_distortion_changes_the_top_ranked_strategy(self) -> None:
        truth = self.report["ground_truth"]
        self.assertEqual(truth["clean_top"], "cleanControl")
        self.assertEqual(truth["observed_top"], "compoundAttack")
        self.assertGreater(truth["observed_ranking_discordance"], 0)

    def test_exact_minimum_uses_three_specialized_channels(self) -> None:
        selected = self.report["synthesis"]["selected"]
        self.assertEqual(
            selected["channels"],
            ["pitDataReceipt", "searchLedger", "evaluationContract"],
        )
        self.assertEqual(selected["cost"], 7)
        self.assertTrue(selected["verifies"])

    def test_complete_evidence_recovers_every_clean_alpha(self) -> None:
        selected = self.report["synthesis"]["selected"]
        self.assertEqual(selected["ranking_discordance"], 0)
        for evaluation in selected["evaluations"]:
            self.assertTrue(evaluation["exact_recovery"])
            self.assertEqual(evaluation["interval_width_bps"], 0)
            self.assertEqual(
                evaluation["certifiable_interval_bps"],
                [evaluation["clean_alpha_bps"], evaluation["clean_alpha_bps"]],
            )

    def test_no_evidence_leaves_the_compound_inflation_unresolved(self) -> None:
        empty = next(
            candidate
            for candidate in self.report["synthesis"]["lower_cost_failures"]
            if candidate["channels"] == []
        )
        compound = next(
            evaluation
            for evaluation in empty["evaluations"]
            if evaluation["experiment"] == "compoundAttack"
        )
        self.assertEqual(compound["interval_width_bps"], 1600)
        self.assertEqual(
            set(compound["unresolved_distortions"]),
            {
                "futureInformation",
                "survivorshipBias",
                "parameterMining",
                "costMutation",
                "benchmarkSwitching",
            },
        )

    def test_every_lower_cost_candidate_has_a_constructive_witness(self) -> None:
        for candidate in self.report["synthesis"]["lower_cost_failures"]:
            self.assertFalse(candidate["verifies"])
            self.assertIn("uncovered", candidate)
            self.assertTrue(candidate["uncovered"]["unresolved_distortions"])

    def test_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["synthesis"]["selected"]["cost"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.benchmark, tampered)

    def test_solver_is_deterministic(self) -> None:
        self.assertEqual(self.report, solve(self.benchmark))


if __name__ == "__main__":
    unittest.main()
