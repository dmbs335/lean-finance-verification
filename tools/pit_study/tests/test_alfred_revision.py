from __future__ import annotations

import copy
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.pit_study.alfred_manifest import build_manifest
from tools.pit_study.alfred_revision import (
    load_config,
    load_package,
    resolve_api_key,
    run_study,
    verify_report,
)
from tools.pit_study.errors import ValidationError

ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "examples" / "alfred_revision_leakage"
CONFIG = EXAMPLE / "config.json"
FIXTURES = EXAMPLE / "fixtures"


class AlfredRevisionLeakageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.fixture_root = Path(self.temporary.name) / "fixtures"
        shutil.copytree(FIXTURES, self.fixture_root)
        self.manifest = self.fixture_root / "manifest.json"
        build_manifest(
            self.fixture_root / "package-spec.json",
            self.manifest,
        )
        self.config = load_config(CONFIG)
        self.package = load_package(self.manifest, self.config)
        self.report = run_study(self.config, self.package)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_release_time_path_is_the_only_strict_pit_path(self) -> None:
        assurance = self.report["assurance"]
        self.assertEqual(
            assurance["release_time_strict_path"],
            "strictPointInTimeAtDecisionInstant",
        )
        self.assertTrue(
            assurance["only_release_time_strict_path_is_strict_point_in_time"]
        )
        self.assertTrue(
            self.report["aggregate"]["all_release_time_strict_inputs_available"]
        )

    def test_date_vintage_can_pass_while_release_time_leaks(self) -> None:
        leaking = [
            item
            for item in self.report["decisions"]
            if item["vintage_date_policy_valid"]
            and not item["vintage_transformation_release_time_valid"]
        ]
        self.assertEqual(
            [item["as_of_date"] for item in leaking],
            ["2020-03-15", "2020-06-15"],
        )
        self.assertEqual(
            self.report["aggregate"]["vintage_only_leakage_decision_count"],
            2,
        )

    def test_two_transformations_are_valid_under_both_policies(self) -> None:
        valid = [
            item
            for item in self.report["decisions"]
            if item["vintage_transformation_release_time_valid"]
        ]
        self.assertEqual(
            [item["as_of_date"] for item in valid],
            ["2020-04-15", "2020-05-15"],
        )
        self.assertEqual(
            self.report["aggregate"]["both_policy_valid_decision_count"],
            2,
        )

    def test_same_day_release_after_decision_is_explicit(self) -> None:
        boundary = {
            item["as_of_date"]: item[
                "same_day_release_after_decision_inputs"
            ]
            for item in self.report["decisions"]
            if item["same_day_release_after_decision_inputs"]
        }
        self.assertEqual(
            boundary,
            {
                "2020-03-15": ["2020-02-01"],
                "2020-06-15": ["2020-05-01"],
            },
        )
        self.assertEqual(
            self.report["aggregate"][
                "same_day_after_decision_boundary_count"
            ],
            2,
        )

    def test_revision_only_path_keeps_release_safe_dates(self) -> None:
        for item in self.report["decisions"]:
            self.assertEqual(
                item["release_time_strict_path"]["observation_dates"],
                item["revision_only_counterfactual"]["observation_dates"],
            )
        self.assertEqual(
            self.report["aggregate"]["selected_value_revision_count"],
            3,
        )
        self.assertEqual(
            self.report["aggregate"]["revision_position_flip_count"],
            3,
        )

    def test_controlled_leakage_components_are_exact(self) -> None:
        aggregate = self.report["aggregate"]
        self.assertEqual(aggregate["vintage_date_total_return_bps"], -103)
        self.assertEqual(
            aggregate["release_time_strict_total_return_bps"], -23
        )
        self.assertEqual(aggregate["revision_only_total_return_bps"], 78)
        self.assertEqual(aggregate["latest_naive_total_return_bps"], -44)
        self.assertEqual(aggregate["intraday_release_leakage_bps"], -80)
        self.assertEqual(aggregate["revision_only_leakage_bps"], 101)
        self.assertEqual(
            aggregate["revision_plus_availability_leakage_bps"], -21
        )

    def test_release_calendar_is_hash_bound(self) -> None:
        calendar = self.fixture_root / "release-calendar.json"
        raw = json.loads(calendar.read_text(encoding="utf-8"))
        raw["releases"][0]["release_at"] = "2020-01-15T15:00:00Z"
        calendar.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "digest mismatch"):
            load_package(self.manifest, self.config)

    def test_manifest_path_escape_is_rejected(self) -> None:
        raw = json.loads(self.manifest.read_text(encoding="utf-8"))
        raw["responses"][0]["relative_path"] = "../outside.json"
        self.manifest.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "unsafe relative path"):
            load_package(self.manifest, self.config)

    def test_api_key_is_required_before_network_access(self) -> None:
        old = os.environ.pop("LFV_MISSING_FRED_KEY", None)
        try:
            with self.assertRaisesRegex(ValidationError, "API key is required"):
                resolve_api_key(None, "LFV_MISSING_FRED_KEY")
        finally:
            if old is not None:
                os.environ["LFV_MISSING_FRED_KEY"] = old

    def test_report_tampering_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["aggregate"]["revision_only_leakage_bps"] = 0
        with self.assertRaisesRegex(ValidationError, "exact recomputation"):
            verify_report(self.config, self.package, tampered)

    def test_study_is_deterministic(self) -> None:
        self.assertEqual(self.report, run_study(self.config, self.package))


if __name__ == "__main__":
    unittest.main()
