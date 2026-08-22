from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.evidence_synth.canonical import canonical_bytes
from tools.evidence_synth.model import load_model
from tools.robust_evidence.errors import ValidationError
from tools.robust_evidence.policy import load_policy
from tools.robust_evidence.solver import (
    evaluate_candidates,
    solve_robust,
    verify_certificate,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = (
    REPOSITORY_ROOT
    / "examples"
    / "robust_evidence"
    / "provider_resilience.model.json"
)
POLICY_PATH = (
    REPOSITORY_ROOT
    / "examples"
    / "robust_evidence"
    / "provider_resilience.policy.json"
)


class RobustEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = load_model(MODEL_PATH)
        self.policy = load_policy(POLICY_PATH, self.model)

    def test_ordinary_optimum_is_not_provider_resilient(self) -> None:
        certificate = solve_robust(self.model, self.policy)
        self.assertEqual(
            certificate["ordinary_optimum"]["channels"],
            ["providerAReceipt1"],
        )
        self.assertEqual(
            certificate["ordinary_optimum"]["weighted_cost"], 1
        )

    def test_robust_optimum_spans_independent_domains(self) -> None:
        certificate = solve_robust(self.model, self.policy)
        self.assertEqual(
            certificate["selected"]["channels"],
            ["providerAReceipt1", "providerBReceipt"],
        )
        self.assertEqual(
            certificate["selected"]["domains"],
            ["providerA", "providerB"],
        )
        self.assertEqual(certificate["selected"]["weighted_cost"], 3)

    def test_same_provider_duplicates_fail_provider_compromise(self) -> None:
        candidates = {item.mask: item for item in evaluate_candidates(
            self.model, self.policy
        )}
        duplicate = candidates[3]
        self.assertFalse(duplicate.verifies)
        self.assertEqual(duplicate.failed_fault, "compromiseProviderA")
        self.assertEqual(duplicate.surviving_channels, ())

    def test_every_lower_cost_candidate_has_fault_and_edge_witness(self) -> None:
        certificate = solve_robust(self.model, self.policy)
        for failure in certificate["lower_cost_failures"]:
            self.assertFalse(failure["verifies"])
            self.assertIn("failed_fault", failure)
            self.assertIn("uncovered_edge", failure)
            self.assertIn("surviving_channels", failure)

    def test_robust_synthesis_is_byte_deterministic(self) -> None:
        first = solve_robust(self.model, self.policy)
        second = solve_robust(self.model, self.policy)
        self.assertEqual(canonical_bytes(first), canonical_bytes(second))

    def test_certificate_tampering_is_rejected(self) -> None:
        certificate = solve_robust(self.model, self.policy)
        tampered = copy.deepcopy(certificate)
        tampered["selected"]["channels"] = [
            "providerAReceipt1",
            "providerAReceipt2",
        ]
        with self.assertRaisesRegex(ValidationError, "exact regeneration"):
            verify_certificate(self.model, self.policy, tampered)

    def test_policy_must_map_every_channel(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing-domain.json"
            raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
            del raw["channel_domains"]["providerBReceipt"]
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "exactly match"):
                load_policy(path, self.model)

    def test_policy_requires_no_fault_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing-none.json"
            raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
            raw["faults"] = [
                item for item in raw["faults"] if item["id"] != "none"
            ]
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "rank-zero"):
                load_policy(path, self.model)


if __name__ == "__main__":
    unittest.main()
