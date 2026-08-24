from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.evidence_taxonomy.fake_alpha import (
    FakeAlphaValidationError,
    evaluate,
    load_benchmark,
    verify,
)

ROOT = Path(__file__).resolve().parents[3]
BENCHMARK = ROOT / "examples" / "fake_alpha_benchmark" / "scenarios.json"


class FakeAlphaBenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.benchmark = load_benchmark(BENCHMARK)
        self.report = evaluate(self.benchmark)
        self.by_id = {
            architecture["id"]: architecture
            for architecture in self.report["architectures"]
        }

    def test_benchmark_contains_six_attacks_and_one_clean_case(self) -> None:
        self.assertEqual(self.report["scenario_count"], 7)
        self.assertEqual(self.report["attack_scenario_count"], 6)

    def test_report_only_evidence_cannot_certify_attack_cases(self) -> None:
        result = self.by_id["reportOnly"]
        self.assertEqual(result["detected_attack_count"], 0)
        self.assertEqual(result["certifiable_scenario_count"], 1)
        self.assertGreater(result["unremoved_attack_bias_bps"], 0)

    def test_provenance_evidence_catches_four_of_six_attacks(self) -> None:
        result = self.by_id["provenanceOnly"]
        self.assertEqual(result["detected_attack_count"], 4)
        missed = {
            scenario["attack"]
            for scenario in result["scenarios"]
            if scenario["attack"] is not None and not scenario["detected"]
        }
        self.assertEqual(missed, {"futureInformation", "hiddenExecution"})

    def test_proof_carrying_architecture_catches_every_attack(self) -> None:
        result = self.by_id["proofCarrying"]
        self.assertEqual(result["detected_attack_count"], 6)
        self.assertEqual(result["certifiable_scenario_count"], 7)
        self.assertEqual(result["unremoved_attack_bias_bps"], 0)
        self.assertTrue(all(
            scenario["interval_contains_economic_alpha"]
            for scenario in result["scenarios"]
        ))

    def test_attack_removal_does_not_equal_economic_alpha(self) -> None:
        result = self.by_id["proofCarrying"]
        clean = next(
            scenario for scenario in result["scenarios"]
            if scenario["id"] == "cleanStrategy"
        )
        self.assertNotEqual(
            clean["cleaned_alpha_bps"], clean["economic_alpha_bps"]
        )
        self.assertTrue(clean["interval_contains_economic_alpha"])

    def test_tampered_report_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["architectures"][-1]["detected_attack_count"] = 0
        with self.assertRaisesRegex(
            FakeAlphaValidationError, "exact recomputation"
        ):
            verify(self.benchmark, tampered)

    def test_evaluation_is_deterministic(self) -> None:
        self.assertEqual(self.report, evaluate(self.benchmark))


if __name__ == "__main__":
    unittest.main()
