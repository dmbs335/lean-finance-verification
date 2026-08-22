from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.pit_study.checker import check, verify
from tools.pit_study.errors import ValidationError
from tools.pit_study.model import load_study

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "examples" / "pit_study" / "momentum_micro_study.json"


class PITStudyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.study = load_study(STUDY)
        self.report = check(self.study)

    def _mutated(self, mutate):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "study.json"
        raw = json.loads(STUDY.read_text(encoding="utf-8"))
        mutate(raw)
        path.write_text(json.dumps(raw), encoding="utf-8")
        return temporary, load_study(path)

    def test_delisted_asset_is_preserved_before_delisting(self) -> None:
        first = self.report["decisions"][0]
        self.assertIn("BETA", first["eligible_assets"])
        self.assertEqual(first["selected"], "BETA")
        last = self.report["decisions"][-1]
        self.assertNotIn("BETA", last["eligible_assets"])

    def test_future_revision_is_rejected(self) -> None:
        temporary, study = self._mutated(
            lambda raw: raw["decisions"][0].update(vintage="prices-v2")
        )
        try:
            with self.assertRaisesRegex(ValidationError, "future dataset vintage"):
                check(study)
        finally:
            temporary.cleanup()

    def test_survivorship_filtered_snapshot_is_rejected(self) -> None:
        temporary, study = self._mutated(
            lambda raw: raw["universe_snapshots"][0]["members"].remove("BETA")
        )
        try:
            with self.assertRaisesRegex(ValidationError, "expected"):
                check(study)
        finally:
            temporary.cleanup()

    def test_delisted_asset_at_cutoff_is_rejected(self) -> None:
        temporary, study = self._mutated(
            lambda raw: raw["universe_snapshots"][-1]["members"].append("BETA")
        )
        try:
            with self.assertRaisesRegex(ValidationError, "expected"):
                check(study)
        finally:
            temporary.cleanup()

    def test_late_corporate_action_is_rejected(self) -> None:
        temporary, study = self._mutated(
            lambda raw: raw["corporate_actions"][0].update(announced_at=42)
        )
        try:
            with self.assertRaisesRegex(ValidationError, "not yet announced"):
                check(study)
        finally:
            temporary.cleanup()

    def test_report_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["decisions"][0]["selected"] = "ALPHA"
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify(self.study, tampered)

    def test_deterministic(self) -> None:
        self.assertEqual(self.report, check(self.study))


if __name__ == "__main__":
    unittest.main()
