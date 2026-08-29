from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.lfv_adapter.bundle import build_from_spec, verify_bundle
from tools.lfv_adapter.bundle_build import compute_code_artifact
from tools.lfv_adapter.canonical import canonical_bytes
from tools.lfv_adapter.errors import ValidationError
from tools.lfv_adapter.spec import load_experiment_spec


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = REPOSITORY_ROOT / "examples" / "reference_adapter"


class BundleTests(unittest.TestCase):
    def test_reference_fixture_executes_and_emits_a_certified_bundle(self) -> None:
        result = build_from_spec(
            FIXTURE / "experiment.json", allow_local_anchor=True
        )
        verify_bundle(result.bundle, allow_local_anchor=True)
        self.assertEqual(result.bundle["claim"]["metric_value"], 400)
        self.assertIn("def certifiedOutput : CertifiedAdapterOutput", result.lean_source)
        self.assertNotIn("sorry", result.lean_source.lower())

    def test_reference_fixture_is_byte_deterministic(self) -> None:
        first = build_from_spec(FIXTURE / "experiment.json", allow_local_anchor=True)
        second = build_from_spec(FIXTURE / "experiment.json", allow_local_anchor=True)
        self.assertEqual(canonical_bytes(first.bundle), canonical_bytes(second.bundle))
        self.assertEqual(first.lean_source, second.lean_source)

    def test_code_identity_is_independent_of_platform_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "fixture"
            shutil.copytree(FIXTURE, copied)
            spec_path = copied / "experiment.json"
            original = load_experiment_spec(spec_path)
            expected = compute_code_artifact(original)

            strategy_path = copied / "strategy.py"
            source = strategy_path.read_text(encoding="utf-8")
            strategy_path.write_bytes(source.replace("\n", "\r\n").encode("utf-8"))
            actual = compute_code_artifact(load_experiment_spec(spec_path))

            self.assertEqual(expected, actual)


    def test_bundle_digest_detects_metadata_tampering(self) -> None:
        result = build_from_spec(FIXTURE / "experiment.json", allow_local_anchor=True)
        tampered = copy.deepcopy(result.bundle)
        tampered["claim"]["metric_value"] += 1
        with self.assertRaisesRegex(ValidationError, "canonical digest mismatch"):
            verify_bundle(tampered, allow_local_anchor=True)

    def test_feature_cannot_depend_on_data_available_after_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "fixture"
            shutil.copytree(FIXTURE, copied)
            spec_path = copied / "experiment.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["features"][0]["generated_at"] = 4
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "generated before dataset"):
                build_from_spec(spec_path, allow_local_anchor=True)


if __name__ == "__main__":
    unittest.main()
