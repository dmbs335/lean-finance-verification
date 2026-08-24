from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.research_agent.candidate import (
    evaluate_candidate_batch,
    load_candidate_batch,
    verify_candidate_batch,
)
from tools.research_agent.errors import ValidationError

ROOT = Path(__file__).resolve().parents[3]
BATCH = ROOT / "examples" / "research_agent" / "candidates.json"


class ResearchCandidateGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.batch = load_candidate_batch(BATCH)
        self.report = evaluate_candidate_batch(self.batch)
        self.by_id = {
            candidate["id"]: candidate
            for candidate in self.report["candidates"]
        }

    def test_decision_distribution_and_no_autonomous_deployment(self) -> None:
        self.assertEqual(
            self.report["decision_counts"],
            {
                "advanceToHumanReview": 1,
                "repairEvidence": 2,
                "rejectCandidate": 2,
            },
        )
        self.assertFalse(self.report["autonomous_deployment_permitted"])

    def test_certifiable_candidate_advances_only_to_human_review(self) -> None:
        candidate = self.by_id["certifiableMomentum"]
        self.assertTrue(candidate["integrity_verified"])
        self.assertEqual(candidate["certifiable_interval_bps"], [40, 80])
        self.assertEqual(candidate["deployable_lower_bound_bps"], 25)
        self.assertEqual(candidate["decision"], "advanceToHumanReview")
        self.assertTrue(candidate["human_approval_required"])

    def test_high_observed_alpha_cannot_bypass_future_data_gap(self) -> None:
        candidate = self.by_id["futureLeakCandidate"]
        self.assertEqual(candidate["observed_alpha_bps"], 120)
        self.assertFalse(candidate["integrity_verified"])
        self.assertEqual(candidate["decision"], "repairEvidence")
        self.assertEqual(
            candidate["minimum_repair"]["channels"],
            ["dataAccessReceipt"],
        )
        self.assertEqual(candidate["minimum_repair"]["cost"], 3)

    def test_combined_parameter_and_cost_repair_is_exact_minimum(self) -> None:
        candidate = self.by_id["parameterAndCostCandidate"]
        self.assertEqual(candidate["decision"], "repairEvidence")
        self.assertEqual(
            candidate["minimum_repair"]["channels"],
            ["evaluationContract", "searchLedger"],
        )
        self.assertEqual(candidate["minimum_repair"]["cost"], 4)

    def test_integrity_valid_but_capacity_dead_candidate_is_rejected(self) -> None:
        candidate = self.by_id["overcrowdedCandidate"]
        self.assertTrue(candidate["integrity_verified"])
        self.assertEqual(candidate["deployable_lower_bound_bps"], -3)
        self.assertEqual(candidate["decision"], "rejectCandidate")
        self.assertFalse(candidate["human_approval_required"])

    def test_unrepresentable_evidence_gap_is_rejected(self) -> None:
        candidate = self.by_id["unobservableCandidate"]
        self.assertFalse(candidate["integrity_verified"])
        self.assertEqual(candidate["minimum_repair"]["status"], "impossible")
        self.assertEqual(candidate["decision"], "rejectCandidate")

    def test_report_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["candidates"][1]["decision"] = "advanceToHumanReview"
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify_candidate_batch(self.batch, tampered)

    def test_candidate_gate_is_deterministic(self) -> None:
        self.assertEqual(
            self.report,
            evaluate_candidate_batch(self.batch),
        )


if __name__ == "__main__":
    unittest.main()
