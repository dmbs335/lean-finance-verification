from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.epistemic_event_study.analyzer import analyze, verify
from tools.epistemic_event_study.model import load_plan
from tools.epistemic_event_study.errors import ValidationError

ROOT = Path(__file__).resolve().parents[3]
PLAN = ROOT / "examples" / "epistemic_event_study" / "vendor_shock.json"


class EpistemicEventStudyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = load_plan(PLAN)
        self.report = analyze(self.plan)

    def _mutated(self, mutate):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "plan.json"
        raw = json.loads(PLAN.read_text(encoding="utf-8"))
        mutate(raw)
        path.write_text(json.dumps(raw), encoding="utf-8")
        return temporary, analyze(load_plan(path))

    def test_registered_matched_event_study_is_accepted(self) -> None:
        self.assertEqual(self.report["status"], "accepted-controlled")
        self.assertIsNotNone(self.report["certificate"])
        self.assertTrue(all(gate["passed"] for gate in self.report["gates"].values()))

    def test_average_event_did_is_850_bps(self) -> None:
        effect = self.report["gates"]["event_effect"]
        self.assertEqual(effect["did_numerator_bps"], 2550)
        self.assertEqual(effect["did_denominator"], 3)
        self.assertEqual(effect["average_did_bps_floor"], 850)

    def test_pairs_are_conventionally_matched_with_flat_pretrends(self) -> None:
        for pair in self.report["pairs"]:
            self.assertTrue(pair["matching_passed"])
            self.assertTrue(pair["treated_exposed"])
            self.assertTrue(pair["control_unexposed"])
            self.assertTrue(pair["pretrend"]["passed"])
            self.assertLessEqual(abs(pair["pretrend"]["did_bps"]), 50)

    def test_late_registration_rejects_certificate(self) -> None:
        temporary, report = self._mutated(
            lambda raw: raw.update(preregistered_at=raw["event_time"])
        )
        try:
            self.assertEqual(report["status"], "rejected")
            self.assertIsNone(report["certificate"])
            self.assertFalse(report["gates"]["preregistration"]["passed"])
        finally:
            temporary.cleanup()

    def test_bad_pretrend_rejects_certificate(self) -> None:
        temporary, report = self._mutated(
            lambda raw: raw["pairs"][0]["treated"].update(
                pre_event_outflow_bps=500
            )
        )
        try:
            self.assertEqual(report["status"], "rejected")
            self.assertFalse(report["gates"]["pretrend"]["passed"])
        finally:
            temporary.cleanup()

    def test_missing_failed_domain_exposure_rejects_matching(self) -> None:
        temporary, report = self._mutated(
            lambda raw: raw["pairs"][0]["treated"].update(
                evidence_domains=["vendor-b"]
            )
        )
        try:
            self.assertEqual(report["status"], "rejected")
            self.assertFalse(report["gates"]["matching"]["passed"])
        finally:
            temporary.cleanup()

    def test_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["gates"]["event_effect"]["average_did_bps_floor"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.plan, tampered)

    def test_analysis_is_deterministic(self) -> None:
        self.assertEqual(self.report, analyze(self.plan))


if __name__ == "__main__":
    unittest.main()
