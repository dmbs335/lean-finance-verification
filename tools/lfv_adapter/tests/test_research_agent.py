from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.lfv_adapter.research_agent import (
    ResearchAgentValidationError,
    evaluate,
    load_batch,
    verify,
)

ROOT = Path(__file__).resolve().parents[3]
BATCH = ROOT / "examples" / "research_agent" / "candidates.json"


class ProofCarryingResearchAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.batch = load_batch(BATCH)
        self.report = evaluate(self.batch)
        self.by_id = {
            candidate["id"]: candidate
            for candidate in self.report["candidates"]
        }

    def test_decision_distribution(self) -> None:
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
        self.assertEqual(candidate["decision"], "advanceToHumanReview")
        self.assertTrue(candidate["integrity_verified"])
        self.assertEqual(candidate["deployable_lower_bound_bps"], 25)
        self.assertTrue(candidate["human_approval_required"])

    def test_high_observed_alpha_does_not_bypass_future_data_gap(self) -> None:
        candidate = self.by_id["futureLeakCandidate"]
        self.assertEqual(candidate["observed_alpha_bps"], 120)
        self.assertFalse(candidate["integrity_verified"])
        self.assertEqual(candidate["decision"], "repairEvidence")
        self.assertEqual(
            candidate["minimum_repair"],
            {
                "status": "synthesized",
                "channels": ["dataAccessReceipt"],
                "cost": 3,
                "unresolved_obligations": [
                    {
                        "id": "futureData",
                        "separators": ["dataAccessReceipt"],
                    }
                ],
            },
        )

    def test_combined_repair_is_exact_minimum(self) -> None:
        candidate = self.by_id["parameterAndCostCandidate"]
        self.assertEqual(candidate["decision"], "repairEvidence")
        self.assertEqual(
            candidate["minimum_repair"]["channels"],
            ["evaluationContract", "searchLedger"],
        )
        self.assertEqual(candidate["minimum_repair"]["cost"], 4)

    def test_verified_but_overcrowded_candidate_is_rejected(self) -> None:
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
        with self.assertRaisesRegex(
            ResearchAgentValidationError, "exact recomputation"
        ):
            verify(self.batch, tampered)

    def test_evaluation_is_deterministic(self) -> None:
        self.assertEqual(self.report, evaluate(self.batch))


if __name__ == "__main__":
    unittest.main()
